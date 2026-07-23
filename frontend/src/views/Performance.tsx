import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchPerformance, pct, PerformanceResponse } from "../api";

const INK_MUTED = "#898781";
const GRID = "#2c2c2a";
const BLUE = "#3987e5";
const TOOLTIP_STYLE = {
  background: "#222221",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 8,
  color: "#fff",
  fontSize: 12.5,
};

export default function Performance() {
  const [data, setData] = useState<PerformanceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Poll so a background boot-refresh (fetch + grade, ~1 min) updates the
    // graded/pending counts without a manual reload.
    let alive = true;
    const load = () =>
      fetchPerformance()
        .then((d) => alive && setData(d))
        .catch((e) => alive && setError(String(e)));
    load();
    const id = setInterval(load, 20000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  if (error) return <div className="error">Performance unavailable: {error}</div>;
  if (!data) return <div className="muted">Loading…</div>;

  const pendingCard = data.n_pending > 0 && (
    <div className="card">
      <h3>Pending grading ({data.n_pending})</h3>
      <div className="sub">
        Games played, outcome not yet graded — refresh the Oracle's Elixir CSV
        in <code>data/</code> and the 12:30 grading run scores these.
        {data.n_voided > 0
          ? ` ${data.n_voided} other pick${data.n_voided === 1 ? "" : "s"} voided (player did not play).`
          : ""}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Player</th>
              <th>Prop</th>
              <th className="num">Line</th>
              <th>Side</th>
              <th className="num">Edge</th>
              <th className="num">vs Book</th>
              <th className="num">Model p(side)</th>
              <th>Match</th>
              <th>Game</th>
            </tr>
          </thead>
          <tbody>
            {data.pending.map((r, i) => {
              const over = r.best_side === "OVER";
              const pSide =
                r.p_over == null ? null : over ? r.p_over : 1 - r.p_over;
              return (
                <tr key={i}>
                  <td>{r.matched_player}</td>
                  <td>
                    {r.prop_type} {r.map_lo}-{r.map_hi}
                  </td>
                  <td className="num">{r.line}</td>
                  <td>
                    <span className={`chip ${over ? "over" : "under"}`}>
                      {r.best_side ?? "—"}
                    </span>
                  </td>
                  <td className="num">{pct(r.best_edge)}</td>
                  <td className="num muted">
                    {r.edge_vs_book == null ? "—" : pct(r.edge_vs_book)}
                  </td>
                  <td className="num">{pct(pSide)}</td>
                  <td className="muted">{r.match_title}</td>
                  <td className="muted">{r.game_time?.slice(0, 10)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );

  if (data.n_graded === 0)
    return (
      <div className="grid">
        {pendingCard}
        <div className="empty">
          <p style={{ fontSize: 16, color: "#c3c2b7" }}>
            No graded picks yet — the track record builds itself.
          </p>
          <p>
            Lines are logged daily (10:00 / 20:00) and graded at 12:30 once the
            Oracle's Elixir CSV covers the match dates. Refresh the 2026 CSV in{" "}
            <code>data/</code> to grade recent matches, then this page fills in:
            hit rate by edge bucket, calibration against real market lines, and
            every graded pick.
          </p>
          <p className="muted">
            Decision rule: bet real money only when the ≥6% edge bucket holds a
            hit rate above ~58% over a few hundred graded picks.
          </p>
        </div>
      </div>
    );

  return (
    <div className="grid">
      <div className="tiles">
        <div className="tile">
          <div className="label">Graded picks</div>
          <div className="value">{data.n_graded}</div>
        </div>
        <div className="tile">
          <div className="label">Overall hit rate</div>
          <div className="value">{pct(data.overall_hit_rate)}</div>
          <div className="hint">break-even ≈ 57.7% at 2-pick 3x</div>
        </div>
        <div className="tile">
          <div className="label">Brier vs market</div>
          <div className="value">{data.brier}</div>
          <div className="hint">coin flip = 0.250, lower is better</div>
        </div>
        <div className="tile">
          <div className="label">Pending grading</div>
          <div className="value">{data.n_pending}</div>
          <div className="hint">
            awaiting outcome data
            {data.n_voided > 0 ? ` · ${data.n_voided} voided (DNP)` : ""}
          </div>
        </div>
      </div>
      {pendingCard}

      <div className="grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <div className="card">
          <h3>Hit rate by edge bucket</h3>
          <div className="sub">
            The validation that matters: bigger claimed edge should mean higher
            hit rate.
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={data.buckets} margin={{ top: 8, right: 8 }}>
              <CartesianGrid stroke={GRID} vertical={false} />
              <XAxis dataKey="bucket" stroke={INK_MUTED} tickLine={false} fontSize={12} />
              <YAxis
                domain={[0, 1]}
                tickFormatter={(v) => `${v * 100}%`}
                stroke={INK_MUTED}
                tickLine={false}
                fontSize={12}
                width={44}
              />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                formatter={(v: number, _n, item) => [
                  `${(v * 100).toFixed(1)}% (n=${item?.payload?.n})`,
                  "hit rate",
                ]}
              />
              <ReferenceLine
                y={0.577}
                stroke={INK_MUTED}
                strokeDasharray="4 4"
                label={{ value: "break-even", fill: INK_MUTED, fontSize: 11, position: "insideTopRight" }}
              />
              <Bar dataKey="hit_rate" fill={BLUE} radius={[4, 4, 0, 0]} maxBarSize={48} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3>Calibration vs market lines</h3>
          <div className="sub">Predicted P(over) vs realized frequency — should hug the diagonal.</div>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart
              data={data.calibration}
              margin={{ top: 8, right: 8 }}
            >
              <CartesianGrid stroke={GRID} />
              <XAxis dataKey="predicted" type="number" domain={[0, 1]} stroke={INK_MUTED} tickLine={false} fontSize={12} tickFormatter={(v) => v.toFixed(1)} />
              <YAxis domain={[0, 1]} stroke={INK_MUTED} tickLine={false} fontSize={12} width={36} tickFormatter={(v) => v.toFixed(1)} />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                formatter={(v: number, name) => [Number(v).toFixed(3), name]}
              />
              <ReferenceLine
                segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]}
                stroke={INK_MUTED}
                strokeDasharray="4 4"
              />
              <Line
                dataKey="actual"
                stroke={BLUE}
                strokeWidth={2}
                dot={{ r: 4, fill: BLUE }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3>Recent graded picks</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Player</th>
                <th>Prop</th>
                <th className="num">Line</th>
                <th>Side</th>
                <th className="num">Edge</th>
                <th className="num">Model p(side)</th>
                <th className="num">Actual</th>
                <th>Result</th>
                <th>Game</th>
              </tr>
            </thead>
            <tbody>
              {data.recent.map((r, i) => {
                const over = r.best_side === "OVER";
                const pSide = over ? r.p_over : 1 - r.p_over;
                const hit = over ? r.outcome_over === 1 : r.outcome_over === 0;
                return (
                  <tr key={i}>
                    <td>{r.matched_player}</td>
                    <td>
                      {r.prop_type} {r.map_lo}-{r.map_hi}
                    </td>
                    <td className="num">{r.line}</td>
                    <td>
                      <span className={`chip ${over ? "over" : "under"}`}>{r.best_side}</span>
                    </td>
                    <td className="num">{pct(r.best_edge)}</td>
                    <td className="num">{pct(pSide)}</td>
                    <td className="num">{r.actual_total}</td>
                    <td style={{ color: hit ? "#0ca30c" : "#e66767", fontWeight: 600 }}>
                      {hit ? "✓ hit" : "✗ miss"}
                    </td>
                    <td className="muted">{r.game_time?.slice(0, 10)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
