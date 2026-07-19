import { useEffect, useMemo, useRef, useState } from "react";
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
import {
  fetchPredict,
  pct,
  PlayerHit,
  PredictResponse,
  searchPlayers,
} from "../api";

const INK_MUTED = "#898781";
const GRID = "#2c2c2a";
const BLUE = "#3987e5";
const RED = "#e66767";
const TOOLTIP_STYLE = {
  background: "#222221",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 8,
  color: "#fff",
  fontSize: 12.5,
};

export default function Explorer() {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<PlayerHit[]>([]);
  const [showDrop, setShowDrop] = useState(false);
  const [player, setPlayer] = useState("");
  const [prop, setProp] = useState("kills");
  const [maps, setMaps] = useState("1-2");
  const [line, setLine] = useState(6.5);
  const [opponent, setOpponent] = useState("");
  const [pred, setPred] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const debounce = useRef<number>();

  useEffect(() => {
    if (!query || query === player) {
      setHits([]);
      return;
    }
    window.clearTimeout(debounce.current);
    debounce.current = window.setTimeout(() => {
      searchPlayers(query).then((h) => {
        setHits(h);
        setShowDrop(true);
      });
    }, 250);
  }, [query, player]);

  const run = async (p = player) => {
    if (!p) return;
    setLoading(true);
    setError(null);
    try {
      setPred(
        await fetchPredict({
          player: p,
          line,
          prop,
          maps,
          opponentTeam: opponent || undefined,
        })
      );
    } catch (e) {
      setPred(null);
      setError(String(e instanceof Error ? e.message : e));
    } finally {
      setLoading(false);
    }
  };

  const histogram = useMemo(() => {
    if (!pred) return [];
    const counts = new Map<number, number>();
    for (const h of pred.history) {
      const b = Math.round(h.total);
      counts.set(b, (counts.get(b) ?? 0) + 1);
    }
    const max = Math.max(...counts.keys());
    return Array.from({ length: max + 1 }, (_, i) => ({
      total: i,
      count: counts.get(i) ?? 0,
    }));
  }, [pred]);

  const recentForm = useMemo(
    () => (pred ? pred.history.slice(-20) : []),
    [pred]
  );

  const over = pred?.prediction === "OVER";

  return (
    <div className="explorer-grid">
      <div className="grid" style={{ alignContent: "start" }}>
        <div className="card">
          <h3>Prediction sandbox</h3>
          <div className="sub">Any player, any line — see the distribution behind the number.</div>
          <div className="grid" style={{ gap: 10 }}>
            <label className="field search-results">
              player
              <input
                placeholder="search player…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={() => hits.length && setShowDrop(true)}
              />
              {showDrop && hits.length > 0 && (
                <div className="search-drop">
                  {hits.map((h) => (
                    <div
                      key={h.player}
                      className="search-item"
                      onClick={() => {
                        setPlayer(h.player);
                        setQuery(h.player);
                        setShowDrop(false);
                        run(h.player);
                      }}
                    >
                      <span>{h.player}</span>
                      <span className="muted">
                        {h.team} · {h.position} · {h.league}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </label>
            <div style={{ display: "flex", gap: 10 }}>
              <label className="field" style={{ flex: 1 }}>
                prop
                <select value={prop} onChange={(e) => setProp(e.target.value)}>
                  <option value="kills">kills</option>
                  <option value="assists">assists</option>
                  <option value="deaths">deaths</option>
                </select>
              </label>
              <label className="field" style={{ flex: 1 }}>
                maps
                <select value={maps} onChange={(e) => setMaps(e.target.value)}>
                  <option value="1-1">map 1</option>
                  <option value="1-2">maps 1-2</option>
                  <option value="1-3">maps 1-3</option>
                </select>
              </label>
              <label className="field" style={{ flex: 1 }}>
                line
                <input
                  type="number"
                  step={0.5}
                  value={line}
                  onChange={(e) => setLine(Number(e.target.value))}
                />
              </label>
            </div>
            <label className="field">
              opponent team <span className="muted">(optional, enables matchup adj.)</span>
              <input
                placeholder="e.g. Gen.G"
                value={opponent}
                onChange={(e) => setOpponent(e.target.value)}
              />
            </label>
            <button className="primary" disabled={!player || loading} onClick={() => run()}>
              {loading ? "Predicting…" : "Predict"}
            </button>
            {error && <div className="error">{error}</div>}
          </div>
        </div>

        {pred && (
          <div className="card">
            <h3>
              {pred.player} · {pred.prop} maps {pred.maps} · line {pred.line}
            </h3>
            <div className={`pred-side ${over ? "over" : "under"}`}>
              {pred.prediction} {pct(pred.side_probability)}
            </div>
            <div className="kv"><span className="k">P(over)</span><span>{pct(pred.p_over)}</span></div>
            <div className="kv"><span className="k">Expected total</span><span>{pred.expected_stat}</span></div>
            <div className="kv">
              <span className="k">90% outcome range</span>
              <span>{pred.predictive_interval[0]} – {pred.predictive_interval[1]}</span>
            </div>
            <div className="kv"><span className="k">Series in sample</span><span>{pred.n_series} (eff. {pred.n_effective})</span></div>
            <div className="kv"><span className="k">Opponent factor</span><span>{pred.opponent_factor}×</span></div>
            <div className="kv">
              <span className="k">Empirical / NegBin blend</span>
              <span>
                {pct(pred.components.p_empirical)} / {pct(pred.components.p_negbinom)} (w={pred.components.w_empirical.toFixed(2)})
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="grid" style={{ alignContent: "start" }}>
        {!pred && (
          <div className="empty">
            Pick a player to see their series-total distribution, the
            probability curve across nearby lines, and recent form.
          </div>
        )}
        {pred && (
          <>
            <div className="card">
              <h3>Series totals distribution</h3>
              <div className="sub">
                {pred.history.length} series · line at {pred.line} marked
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={histogram} margin={{ top: 8, right: 8 }}>
                  <CartesianGrid stroke={GRID} vertical={false} />
                  <XAxis dataKey="total" stroke={INK_MUTED} tickLine={false} fontSize={12} />
                  <YAxis allowDecimals={false} stroke={INK_MUTED} tickLine={false} fontSize={12} width={30} />
                  <Tooltip
                    contentStyle={TOOLTIP_STYLE}
                    formatter={(v: number) => [v, "series"]}
                    labelFormatter={(l) => `total = ${l}`}
                  />
                  <ReferenceLine x={pred.line} stroke={RED} strokeWidth={2} strokeDasharray="4 3"
                    label={{ value: `line ${pred.line}`, fill: RED, fontSize: 11, position: "top" }} />
                  <Bar dataKey="count" fill={BLUE} radius={[4, 4, 0, 0]} maxBarSize={28} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h3>P(over) across lines</h3>
              <div className="sub">how the probability moves as the line moves</div>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={pred.curve} margin={{ top: 8, right: 8 }}>
                  <CartesianGrid stroke={GRID} />
                  <XAxis dataKey="line" stroke={INK_MUTED} tickLine={false} fontSize={12} />
                  <YAxis domain={[0, 1]} tickFormatter={(v) => `${v * 100}%`} stroke={INK_MUTED} tickLine={false} fontSize={12} width={40} />
                  <Tooltip
                    contentStyle={TOOLTIP_STYLE}
                    formatter={(v: number) => [`${(v * 100).toFixed(1)}%`, "P(over)"]}
                    labelFormatter={(l) => `line ${l}`}
                  />
                  <ReferenceLine y={0.5} stroke={INK_MUTED} strokeDasharray="4 4" />
                  <ReferenceLine x={pred.line} stroke={RED} strokeDasharray="4 3" />
                  <Line dataKey="p_over" stroke={BLUE} strokeWidth={2} dot={{ r: 3, fill: BLUE }} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h3>Recent form</h3>
              <div className="sub">last {recentForm.length} series totals</div>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={recentForm} margin={{ top: 8, right: 8 }}>
                  <CartesianGrid stroke={GRID} vertical={false} />
                  <XAxis dataKey="date" stroke={INK_MUTED} tickLine={false} fontSize={11} interval="preserveStartEnd" />
                  <YAxis allowDecimals={false} stroke={INK_MUTED} tickLine={false} fontSize={12} width={30} />
                  <Tooltip
                    contentStyle={TOOLTIP_STYLE}
                    formatter={(v: number) => [v, pred.prop]}
                  />
                  <ReferenceLine y={pred.line} stroke={RED} strokeDasharray="4 3" />
                  <Bar dataKey="total" fill={BLUE} radius={[4, 4, 0, 0]} maxBarSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
