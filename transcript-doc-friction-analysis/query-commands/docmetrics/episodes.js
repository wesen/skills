// docmetrics episodes — slice sessions into episodes at real user
// instructions; per-episode tool mix, failures, wall time and idle gaps.
//
// "Real" user turns exclude tool-result carriers (NULL content_type trap:
// claude-code human turns have NULL content_type, so filter with COALESCE),
// local-command wrappers (<command-name>, <local-command-*>), skill
// injections ("Base directory for this skill"), image attachments, and
// compaction summaries ("This session is being continued").

const openDb = function() {
  const mt = require("minitrace");
  return mt.db().RuntimeArchives().QueryCommandDefaults()
    .Limits(mt.limits().Rows(200000).CellChars(4000).Build())
    .Build();
}

const isRealInstruction = function(content) {
  const c = (content || "").trim();
  if (!c) return false;
  if (c.startsWith("<")) return false;
  if (c.startsWith("[Image")) return false;
  if (c.startsWith("Base directory for this skill")) return false;
  if (c.startsWith("This session is being continued")) return false;
  if (c.startsWith("Caveat:")) return false;
  return true;
}

function episodes() {
  const db = openDb();
  try {
    const users = db.query(`
      SELECT session_id, turn_index, timestamp, substr(COALESCE(content,''),1,300) AS content
      FROM turns
      WHERE role = 'user' AND COALESCE(content_type,'') != 'tool_result'
      ORDER BY session_id, turn_index
    `);
    const calls = db.query(`
      SELECT session_id, emitting_turn_index AS turn, timestamp, tool_name, success
      FROM tool_calls ORDER BY session_id, timestamp
    `);

    const boundaries = {}; // session -> [{turn, timestamp, content}]
    for (const u of users) {
      if (!isRealInstruction(u.content)) continue;
      (boundaries[u.session_id] = boundaries[u.session_id] || []).push(u);
    }

    const out = [];
    for (const [sid, bs] of Object.entries(boundaries)) {
      const sessionCalls = calls.filter((c) => c.session_id === sid);
      for (let i = 0; i < bs.length; i++) {
        const start = bs[i].turn_index;
        const end = i + 1 < bs.length ? bs[i + 1].turn_index : Infinity;
        const eps = sessionCalls.filter((c) => c.turn >= start && c.turn < end);
        const tools = {};
        let failures = 0;
        for (const c of eps) {
          tools[c.tool_name] = (tools[c.tool_name] || 0) + 1;
          if (!c.success) failures++;
        }
        // Wall time + idle-gap detection (gaps > 10 min between calls).
        let wallMin = 0, idleMin = 0;
        if (eps.length > 1) {
          const t0 = Date.parse(eps[0].timestamp), t1 = Date.parse(eps[eps.length - 1].timestamp);
          wallMin = Math.round((t1 - t0) / 60000);
          for (let k = 1; k < eps.length; k++) {
            const gap = (Date.parse(eps[k].timestamp) - Date.parse(eps[k - 1].timestamp)) / 60000;
            if (gap > 10) idleMin += Math.round(gap);
          }
        }
        out.push({
          session_id: sid,
          episode: i + 1,
          start_turn: start,
          end_turn: end === Infinity ? null : end - 1,
          instruction: bs[i].content.slice(0, 120),
          tool_calls: eps.length,
          failures,
          wall_min: wallMin,
          idle_min: idleMin,
          top_tools: Object.entries(tools).sort((a, b) => b[1] - a[1]).slice(0, 4)
            .map(([t, n]) => `${t}:${n}`).join(" "),
        });
      }
    }
    return out;
  } finally {
    db.close();
  }
}

__verb__("episodes", {
  name: "episodes",
  short: "Slice sessions into episodes at real user instructions; tool mix + idle gaps",
});
