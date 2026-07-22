// docmetrics failure-triage — root-cause classification of failed tool calls.
//
// Classifier rules derived from adversarial verification of a real session
// (GOGO-DOCS-OPTIMIZE-2026-07-19, report S5). Precedence order matters:
//  1. self-kill      exit 143/144 + pkill/pgrep in command (the pattern often
//                    matches the harness shell's own command line and kills
//                    the tool call; flagged when the killed pattern appears
//                    literally elsewhere in the same command)
//  2. zsh-expansion  "(eval): ... not found" from unquoted =words (echo ===)
//  3. read-before-edit  harness Write/Edit guard
//  4. nul-byte       illegal character NUL in source
//  5. cwd-drift      "No such file" on a relative path after an earlier cd in
//                    the same session left the persistent shell elsewhere
//  6. missing-file   other no-such-file (incl. hallucinated paths)
//  7. timeout        command timed out
//  8. go-compile / go-test  real compiler/test errors in the output
//  9. partial-success   exit != 0 but the payload the command was for is
//                    present in the result
// 10. nonzero-exit  everything else

const openDb = function() {
  const mt = require("minitrace");
  return mt.db().RuntimeArchives().QueryCommandDefaults()
    .Limits(mt.limits().Rows(200000).CellChars(4000).Build())
    .Build();
}

const classify = function(row, lastCd) {
  const cmd = row.command || "";
  const text = ((row.error || "") + "\n" + (row.result || ""));
  const lower = text.toLowerCase();

  if ((/pkill|pgrep/.test(cmd)) && (row.exit_code === 144 || row.exit_code === 143 || lower.includes("exit code 144"))) {
    const m = cmd.match(/p(?:kill|grep)\s+(?:-[\w]+\s+)*["']?([^"'\s;|&]+)/);
    const pat = m ? m[1] : null;
    const selfMatch = pat && cmd.split(pat).length > 2;
    return { category: "self-kill", detail: selfMatch ? `pattern "${pat}" also appears in own command line` : "pkill/pgrep kill chain" };
  }
  if (/\(eval\).*not found/.test(text) || /^==+ not found/m.test(text)) {
    return { category: "zsh-expansion", detail: "unquoted =word (e.g. echo ===) aborted the compound" };
  }
  if (lower.includes("has not been read yet")) {
    return { category: "read-before-edit", detail: "Write/Edit on unread file (often a scaffolded stub)" };
  }
  if (lower.includes("illegal character nul") || lower.includes("\\x00")) {
    return { category: "nul-byte", detail: "NUL byte in source (heredoc/Write encoding)" };
  }
  if (lower.includes("no such file")) {
    const relTarget = /(?:can't read|cannot stat|no such file[^:]*:?)\s+([^\s:']+)/i.exec(text);
    const target = relTarget ? relTarget[1] : "";
    if (target && !target.startsWith("/") && lastCd) {
      return { category: "cwd-drift", detail: `relative path "${target}" after earlier cd to ${lastCd}` };
    }
    return { category: "missing-file", detail: target || "path not found" };
  }
  if (lower.includes("timed out")) return { category: "timeout", detail: "" };
  if (/^--- fail|\nfail\t/m.test(lower)) return { category: "go-test", detail: "" };
  if (/\.go:\d+:\d+:/.test(text) && /(undefined:|cannot use|declared and not used|syntax error)/.test(text)) {
    return { category: "go-compile", detail: "" };
  }
  const hasPayload = (row.result || "").length > 200 && !lower.includes("error");
  if (hasPayload) return { category: "partial-success", detail: "payload delivered despite non-zero exit" };
  return { category: "nonzero-exit", detail: "" };
}

function failureTriage() {
  const db = openDb();
  try {
    // Pull all Bash commands to track persistent-shell cd state per session.
    const allBash = db.query(`
      SELECT session_id, emitting_turn_index AS turn, substr(command,1,300) AS command
      FROM tool_calls WHERE tool_name IN ('Bash','bash','shell','exec') ORDER BY session_id, timestamp
    `);
    const cdState = {}; // session -> [{turn, dir}]
    for (const r of allBash) {
      const m = /(?:^|;|&&)\s*cd\s+([^\s;|&]+)\s*$/.exec(r.command) || /(?:^|;|&&)\s*cd\s+([^\s;|&]+)\s*(?:;|&&)/.exec(r.command);
      if (m) (cdState[r.session_id] = cdState[r.session_id] || []).push({ turn: r.turn, dir: m[1] });
    }
    const lastCdBefore = (sid, turn) => {
      const list = cdState[sid] || [];
      let last = null;
      for (const c of list) { if (c.turn < turn) last = c.dir; else break; }
      return last;
    };

    const rows = db.query(`
      SELECT session_id, tool_call_id, emitting_turn_index AS turn, timestamp,
             tool_name, exit_code, substr(command,1,400) AS command,
             file_path,
             substr(COALESCE(error,''),1,500) AS error,
             substr(COALESCE(result,''),1,500) AS result
      FROM tool_calls WHERE success = 0 ORDER BY session_id, timestamp
    `);

    const byCategory = {};
    const out = rows.map((r) => {
      const c = classify(r, lastCdBefore(r.session_id, r.turn));
      byCategory[c.category] = (byCategory[c.category] || 0) + 1;
      return {
        session_id: r.session_id,
        turn: r.turn,
        tool: r.tool_name,
        category: c.category,
        detail: c.detail,
        command: (r.command || r.file_path || "").slice(0, 120),
      };
    });

    return { total: rows.length, byCategory, failures: out };
  } finally {
    db.close();
  }
}

__verb__("failureTriage", {
  name: "failure-triage",
  short: "Root-cause classification of failed tool calls (self-kill, cwd-drift, zsh-expansion, ...)",
});
