import { useEffect, useMemo, useState } from "react";
import { BoardResponse, fetchBoard, pct } from "../api";

function fmtTime(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    weekday: "short",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function Board() {
  const [data, setData] = useState<BoardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [minEdge, setMinEdge] = useState(0.03);
  const [query, setQuery] = useState("");

  useEffect(() => {
    fetchBoard().then(setData).catch((e) => setError(String(e)));
  }, []);

  const rows = useMemo(() => {
    if (!data) return [];
    // team_ok=false means possible name collision - never show as a pick
    let r = data.lines.filter((l) => l.matched_player != null && l.team_ok !== false);
    if (minEdge > -1) r = r.filter((l) => (l.best_edge ?? -1) >= minEdge);
    if (query)
      r = r.filter(
        (l) =>
          l.matched_player!.toLowerCase().includes(query.toLowerCase()) ||
          (l.match_title ?? "").toLowerCase().includes(query.toLowerCase())
      );
    return r;
  }, [data, minEdge, query]);

  if (error) return <div className="error">Board unavailable: {error}</div>;
  if (!data) return <div className="muted">Loading board…</div>;
  if (!data.snapshot_ts)
    return (
      <div className="empty">
        No lines logged yet. Run <code>scripts/log_lines.py</code> (scheduled
        daily at 10:00 / 20:00) to snapshot the live board.
      </div>
    );

  const nEdged = data.lines.filter((l) => (l.best_edge ?? -1) >= 0.03).length;
  const maxEdge = Math.max(0.001, ...rows.map((r) => r.best_edge ?? 0));

  return (
    <div className="grid">
      <div className="tiles">
        <div className="tile">
          <div className="label">Snapshot</div>
          <div className="value" style={{ fontSize: 18 }}>
            {new Date(data.snapshot_ts).toLocaleString()}
          </div>
          <div className="hint">latest board pull</div>
        </div>
        <div className="tile">
          <div className="label">Lines on board</div>
          <div className="value">{data.n_lines}</div>
          <div className="hint">matched to model: {data.lines.filter((l) => l.matched_player).length}</div>
        </div>
        <div className="tile">
          <div className="label">Picks ≥ 3% edge</div>
          <div className="value">{nEdged}</div>
          <div className="hint">vs per-leg break-even</div>
        </div>
      </div>

      <div className="card">
        <h3>Upcoming lines</h3>
        <div className="sub">
          Latest snapshot of each line for games that haven't started; past
          games move to the Track record. "vs Book" is how much likelier the
          model thinks our side is than the book's own no-vig probability.
        </div>
        <div className="controls">
          <label className="field">
            min edge
            <select
              value={minEdge}
              onChange={(e) => setMinEdge(Number(e.target.value))}
            >
              <option value={-1}>all lines</option>
              <option value={0}>0%+</option>
              <option value={0.03}>3%+</option>
              <option value={0.06}>6%+</option>
              <option value={0.1}>10%+</option>
            </select>
          </label>
          <label className="field">
            search
            <input
              placeholder="player or match…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Side</th>
                <th>Player</th>
                <th>Prop</th>
                <th className="num">Line</th>
                <th className="num">Model p</th>
                <th className="num">Book p</th>
                <th className="num">Break-even</th>
                <th className="num">Edge</th>
                <th className="num">vs Book</th>
                <th className="num">Exp</th>
                <th className="num">n</th>
                <th className="num">Opp ×</th>
                <th>Match</th>
                <th>Start</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((l, i) => {
                const over = l.best_side === "OVER";
                const pSide =
                  l.p_over == null ? null : over ? l.p_over : 1 - l.p_over;
                const bookSide =
                  l.book_p_over == null
                    ? null
                    : over
                      ? l.book_p_over
                      : 1 - l.book_p_over;
                const be = over ? l.breakeven_over : l.breakeven_under;
                const edge = l.best_edge ?? 0;
                return (
                  <tr key={i}>
                    <td>
                      <span className={`chip ${over ? "over" : "under"}`}>
                        {l.best_side ?? "—"}
                      </span>
                    </td>
                    <td>
                      {l.matched_player}
                      <span className="muted"> · {l.own_team}</span>
                    </td>
                    <td>
                      {l.prop_type} {l.map_lo}-{l.map_hi}
                    </td>
                    <td className="num">{l.line}</td>
                    <td className="num">{pct(pSide)}</td>
                    <td className="num muted">{pct(bookSide)}</td>
                    <td className="num muted">{pct(be)}</td>
                    <td className="num">
                      <span className="edge-cell">
                        <span
                          className="edge-bar"
                          style={{
                            width: `${Math.max(2, (edge / maxEdge) * 48)}px`,
                            opacity: edge > 0 ? 1 : 0.25,
                          }}
                        />
                        <span className={edge >= 0.03 ? "edge-pos" : "edge-neg"}>
                          {edge >= 0 ? "+" : ""}
                          {pct(edge)}
                        </span>
                      </span>
                    </td>
                    <td className="num">
                      <span
                        className={
                          (l.edge_vs_book ?? 0) >= 0.03 ? "edge-pos" : "edge-neg"
                        }
                      >
                        {l.edge_vs_book == null
                          ? "—"
                          : `${l.edge_vs_book >= 0 ? "+" : ""}${pct(l.edge_vs_book)}`}
                      </span>
                    </td>
                    <td className="num">{l.expected_stat}</td>
                    <td className="num muted">{l.n_series}</td>
                    <td className="num muted">{l.opponent_factor}</td>
                    <td className="muted">{l.match_title}</td>
                    <td className="muted">{fmtTime(l.game_time)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {rows.length === 0 && (
            <div className="empty" style={{ marginTop: 12 }}>
              No lines match the current filter.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
