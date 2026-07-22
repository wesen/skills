// docmetrics doc-consumption — per-session documentation-consumption profile.
//
// Measures how a coding session consumed documentation: Skill tool loads,
// skill files sideloaded via Bash (cat/sed/head of ~/.claude/skills — these
// are invisible to Read-based counting), embedded `<app> help <topic>`
// invocations, reads of embedded doc corpora (pkg/doc, doc/topics), and
// markdown reads split into ticket docs vs other.
//
// Run:
//   go-minitrace query commands --query-repository <skill>/query-commands \
//     docmetrics doc-consumption --archive-glob '<archives>/active/*/*.minitrace.json' \
//     --output json


// Cross-framework command extraction: claude-code populates `command`;
// pi uses lowercase tool names with `command`; codex buries shell commands
// as JS strings (tools.exec_command({cmd: "..."})) inside arguments_json.
const SHELL_TOOLS = "('Bash','bash','shell','exec','run_terminal_cmd')";
const effectiveCommands = function(row) {
  if (row.command && row.command.length) return [row.command];
  const aj = row.arguments_json || "";
  const out = [];
  const re = /(?:\\?"?cmd\\?"?|\\?"command\\?")\s*:\s*\\?"((?:[^"\\]|\\.)*)\\?"/g;
  let m;
  while ((m = re.exec(aj)) !== null) {
    out.push(m[1].replace(/\\n/g, "\n").replace(/\\"/g, '"').slice(0, 500));
  }
  return out;
};

const openDb = function() {
  const mt = require("minitrace");
  return mt.db().RuntimeArchives().QueryCommandDefaults()
    .Limits(mt.limits().Rows(200000).CellChars(4000).Build())
    .Build();
}

const parseSkillName = function(argsJson) {
  try {
    const a = JSON.parse(argsJson);
    return a.skill || a.name || null;
  } catch (e) {
    return null;
  }
}

// Classify a Bash command's help usage. Returns list of {app, topic} for
// embedded-help invocations (`app help topic`), skipping `--help` flag checks
// and common false positives (a word "help" inside strings/paths).
const extractHelpInvocations = function(cmd) {
  const out = [];
  // Command-position only: string start or after a shell operator — prose
  // inside echo/commit messages ("... in help topic ...") must not match.
  const re = /(?:^|[;&|(]\s*)([a-zA-Z][\w./-]*)\s+help\s+([\w-]{3,})/g;
  const stoplist = { git: 1, man: 1, echo: 1, in: 1, the: 1, for: 1, with: 1, embedded: 1, a: 1, an: 1 };
  let m;
  while ((m = re.exec(cmd)) !== null) {
    const app = m[1].split("/").pop();
    const topic = m[2];
    if (stoplist[app]) continue;
    out.push({ app, topic });
  }
  return out;
}

function docConsumption() {
  const db = openDb();
  try {
    const sessions = db.query(`
      SELECT session_id, title, working_directory, started_at, tool_call_count
      FROM sessions ORDER BY started_at
    `);

    const skillCalls = db.query(`
      SELECT session_id, emitting_turn_index AS turn, arguments_json
      FROM tool_calls WHERE tool_name = 'Skill' ORDER BY timestamp
    `);

    const sideloads = db.query(`
      SELECT session_id, emitting_turn_index AS turn, substr(COALESCE(command,''),1,200) AS command,
             substr(COALESCE(arguments_json,''),1,1500) AS arguments_json
      FROM tool_calls
      WHERE tool_name IN ('Bash','bash','shell','exec')
        AND (command LIKE '%.claude/skills%' OR command LIKE '%.codex/skills%' OR command LIKE '%.pi/skills%'
             OR arguments_json LIKE '%.claude/skills%' OR arguments_json LIKE '%.codex/skills%' OR arguments_json LIKE '%.pi/skills%')
      ORDER BY timestamp
    `);

    const helpCandidates = db.query(`
      SELECT session_id, emitting_turn_index AS turn, substr(COALESCE(command,''),1,400) AS command,
             substr(COALESCE(arguments_json,''),1,2000) AS arguments_json
      FROM tool_calls
      WHERE tool_name IN ('Bash','bash','shell','exec')
        AND (command LIKE '% help %' OR arguments_json LIKE '% help %')
      ORDER BY timestamp
    `);

    const embeddedDocReads = db.query(`
      SELECT session_id, emitting_turn_index AS turn, tool_name,
             COALESCE(file_path, substr(command,1,200)) AS what
      FROM tool_calls
      WHERE (COALESCE(file_path,'') LIKE '%pkg/doc/%' AND file_path LIKE '%.md')
         OR (COALESCE(file_path,'') LIKE '%doc/topics/%')
         OR (tool_name IN ('Bash','bash','shell','exec')
             AND (COALESCE(command,arguments_json,'') LIKE '%pkg/doc/%' OR COALESCE(command,arguments_json,'') LIKE '%doc/topics/%')
             AND (COALESCE(command,arguments_json,'') LIKE '%cat %' OR COALESCE(command,arguments_json,'') LIKE '%head %'
                  OR COALESCE(command,arguments_json,'') LIKE '%sed -n%' OR COALESCE(command,arguments_json,'') LIKE '%ls %'))
      ORDER BY timestamp
    `);

    const mdReads = db.query(`
      SELECT session_id, file_path FROM tool_calls
      WHERE tool_name IN ('Read','read') AND COALESCE(file_path,'') LIKE '%.md'
    `);

    // Skill files consumed via the Read tool (Pi reads ~/.pi/agent/skills/...,
    // Claude sometimes Reads SKILL.md directly) — invisible to Bash-sideload
    // and Skill-tool counting.
    const skillFileReads = db.query(`
      SELECT session_id, emitting_turn_index AS turn, file_path
      FROM tool_calls
      WHERE tool_name IN ('Read','read')
        AND (file_path LIKE '%/skills/%' OR file_path LIKE '%SKILL.md%')
      ORDER BY timestamp
    `);

    // Codex md reads: sed/cat/head of *.md inside JS-embedded exec commands.
    const codexMdReads = db.query(`
      SELECT session_id, COUNT(*) AS n
      FROM tool_calls
      WHERE tool_name = 'exec' AND COALESCE(command,'') = ''
        AND arguments_json LIKE '%.md%'
        AND (arguments_json LIKE '%sed -n%' OR arguments_json LIKE '%cat %' OR arguments_json LIKE '%head %')
      GROUP BY session_id
    `);

    const profiles = {};
    for (const s of sessions) {
      profiles[s.session_id] = {
        session_id: s.session_id,
        title: (s.title || "").slice(0, 60),
        working_directory: s.working_directory,
        started_at: s.started_at,
        tool_calls: s.tool_call_count,
        skill_loads: [],
        skill_sideloads: [],
        embedded_help_invocations: [],
        help_flag_or_other: 0,
        embedded_doc_reads: [],
        md_reads_ticket: 0,
        md_reads_other: 0,
        skill_file_reads: [],
        exec_md_read_cmds: 0,
      };
    }
    const p = (sid) => profiles[sid] || (profiles[sid] = { session_id: sid });

    for (const r of skillCalls) {
      p(r.session_id).skill_loads.push({ turn: r.turn, skill: parseSkillName(r.arguments_json) });
    }
    for (const r of sideloads) {
      const cmd = effectiveCommands(r).join(" && ").slice(0, 200);
      p(r.session_id).skill_sideloads.push({ turn: r.turn, command: cmd });
    }
    for (const r of helpCandidates) {
      const invs = effectiveCommands(r).flatMap((c) => extractHelpInvocations(c));
      if (invs.length) {
        for (const inv of invs) {
          p(r.session_id).embedded_help_invocations.push({ turn: r.turn, ...inv });
        }
      } else {
        p(r.session_id).help_flag_or_other++;
      }
    }
    for (const r of embeddedDocReads) {
      p(r.session_id).embedded_doc_reads.push({ turn: r.turn, what: r.what });
    }
    for (const r of mdReads) {
      if ((r.file_path || "").includes("/ttmp/")) p(r.session_id).md_reads_ticket++;
      else p(r.session_id).md_reads_other++;
    }
    for (const r of skillFileReads) {
      p(r.session_id).skill_file_reads.push({ turn: r.turn, file: r.file_path });
    }
    for (const r of codexMdReads) {
      p(r.session_id).exec_md_read_cmds = r.n;
    }

    // Compact summary row per session for quick comparison tables.
    const summary = Object.values(profiles).map((x) => ({
      session_id: x.session_id,
      title: x.title,
      tool_calls: x.tool_calls,
      skill_loads: (x.skill_loads || []).length,
      skill_names: (x.skill_loads || []).map((s) => s.skill).join(","),
      skill_sideloads: (x.skill_sideloads || []).length,
      skill_file_reads: (x.skill_file_reads || []).length,
      exec_md_read_cmds: x.exec_md_read_cmds || 0,
      embedded_help_calls: (x.embedded_help_invocations || []).length,
      embedded_doc_reads: (x.embedded_doc_reads || []).length,
      md_reads_ticket: x.md_reads_ticket,
      md_reads_other: x.md_reads_other,
    }));

    return { summary, profiles };
  } finally {
    db.close();
  }
}

__verb__("docConsumption", {
  name: "doc-consumption",
  short: "Per-session documentation-consumption profile (skills, help, doc reads)",
});
