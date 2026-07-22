// docmetrics api-calls — deduplicated token accounting + context trajectory.
//
// CRITICAL CAVEAT this verb exists to fix: the claude-code adapter stores one
// turns row per content BLOCK; consecutive assistant rows emitted by one API
// call repeat identical usage numbers, so naive SUM() over turns overcounts
// tokens by ~2-2.5x. This verb collapses consecutive assistant rows with an
// identical (output, cache_read, cache_creation) tuple into one logical API
// call and reports both accountings, the context-size trajectory, and
// detected compaction events (>80% collapse of cache_read per call).

const openDb = function() {
  const mt = require("minitrace");
  return mt.db().RuntimeArchives().QueryCommandDefaults()
    .Limits(mt.limits().Rows(200000).CellChars(4000).Build())
    .Build();
}

function apiCalls() {
  const db = openDb();
  try {
    const rows = db.query(`
      SELECT session_id, turn_index,
             COALESCE(output_tokens,0) AS out,
             COALESCE(cache_read_tokens,0) AS cr,
             COALESCE(cache_creation_tokens,0) AS cc,
             COALESCE(input_tokens,0) AS inp
      FROM turns
      WHERE role = 'assistant'
      ORDER BY session_id, turn_index
    `);

    const bySession = {};
    for (const r of rows) {
      const s = (bySession[r.session_id] = bySession[r.session_id] || {
        naive: { out: 0, cr: 0, cc: 0, rows: 0 },
        calls: [],
        last: null,
      });
      s.naive.out += r.out;
      s.naive.cr += r.cr;
      s.naive.cc += r.cc;
      s.naive.rows++;
      const key = r.out + "|" + r.cr + "|" + r.cc;
      if (s.last && s.last.key === key && r.turn_index - s.last.end_turn <= 3) {
        s.last.end_turn = r.turn_index;
      } else {
        const call = { start_turn: r.turn_index, end_turn: r.turn_index, key, out: r.out, cr: r.cr, cc: r.cc, inp: r.inp };
        s.calls.push(call);
        s.last = call;
      }
    }

    const out = [];
    for (const [sid, s] of Object.entries(bySession)) {
      const dedup = { out: 0, cr: 0, cc: 0 };
      for (const c of s.calls) {
        dedup.out += c.out;
        dedup.cr += c.cr;
        dedup.cc += c.cc;
      }
      // Context trajectory: cache_read per call, sampled every ~25 calls.
      const traj = [];
      for (let i = 0; i < s.calls.length; i += Math.max(1, Math.floor(s.calls.length / 20))) {
        traj.push({ turn: s.calls[i].start_turn, context: s.calls[i].cr });
      }
      // Compaction detection: cache_read collapses >80% vs previous call
      // while previous context was substantial.
      const compacts = [];
      for (let i = 1; i < s.calls.length; i++) {
        const prev = s.calls[i - 1], cur = s.calls[i];
        if (prev.cr > 100000 && cur.cr < prev.cr * 0.2) {
          compacts.push({ turn: cur.start_turn, before: prev.cr, after: cur.cr });
        }
      }
      out.push({
        session_id: sid,
        api_calls: s.calls.length,
        turn_rows: s.naive.rows,
        inflation_factor: s.naive.out > 0 ? +(s.naive.out / Math.max(1, dedup.out)).toFixed(2) : 1,
        naive: s.naive,
        deduped: dedup,
        compaction_events: compacts,
        context_trajectory: traj,
      });
    }
    return out;
  } finally {
    db.close();
  }
}

__verb__("apiCalls", {
  name: "api-calls",
  short: "Deduplicated per-API-call token totals, context trajectory, compaction events",
});
