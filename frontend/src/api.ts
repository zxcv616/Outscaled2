export interface BoardLine {
  player_name: string;
  matched_player: string | null;
  own_team: string | null;
  team_ok: boolean | null;
  prop_type: string;
  map_lo: number;
  map_hi: number;
  line: number;
  payout_over: number | null;
  payout_under: number | null;
  game_time: string | null;
  match_title: string | null;
  p_over: number | null;
  expected_stat: number | null;
  n_series: number | null;
  opponent_factor: number | null;
  breakeven_over: number | null;
  breakeven_under: number | null;
  edge_over: number | null;
  edge_under: number | null;
  best_side: "OVER" | "UNDER" | null;
  best_edge: number | null;
}

export interface BoardResponse {
  snapshot_ts: string | null;
  n_lines: number;
  lines: BoardLine[];
}

export interface CalibrationBin {
  bin: string;
  predicted: number;
  actual: number;
  n: number;
}

export interface EdgeBucket {
  bucket: string;
  n: number;
  hit_rate: number;
}

export interface GradedPick {
  matched_player: string;
  prop_type: string;
  map_lo: number;
  map_hi: number;
  line: number;
  best_side: string;
  best_edge: number | null;
  p_over: number;
  actual_total: number;
  outcome_over: number;
  game_time: string;
}

export interface PerformanceResponse {
  n_graded: number;
  brier?: number;
  overall_hit_rate?: number;
  buckets: EdgeBucket[];
  calibration: CalibrationBin[];
  recent: GradedPick[];
}

export interface PlayerHit {
  player: string;
  team: string;
  position: string;
  league: string;
  last_played: string;
}

export interface PredictResponse {
  player: string;
  line: number;
  prediction: "OVER" | "UNDER";
  p_over: number;
  side_probability: number;
  expected_stat: number;
  predictive_interval: [number, number];
  expected_stat_ci: [number, number];
  n_series: number;
  n_effective: number;
  opponent_factor: number;
  components: { p_empirical: number; p_negbinom: number; w_empirical: number };
  history: { date: string; total: number }[];
  curve: { line: number; p_over: number }[];
  prop: string;
  maps: string;
}

async function get<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const fetchBoard = () => get<BoardResponse>("/api/board");
export const fetchPerformance = () => get<PerformanceResponse>("/api/performance");
export const searchPlayers = (q: string) =>
  get<PlayerHit[]>(`/api/players?q=${encodeURIComponent(q)}`);
export const fetchPredict = (p: {
  player: string;
  line: number;
  prop: string;
  maps: string;
  opponentTeam?: string;
}) =>
  get<PredictResponse>(
    `/api/predict?player=${encodeURIComponent(p.player)}&line=${p.line}` +
      `&prop=${p.prop}&maps=${p.maps}` +
      (p.opponentTeam ? `&opponent_team=${encodeURIComponent(p.opponentTeam)}` : "")
  );

export const pct = (x: number | null | undefined, digits = 1) =>
  x == null ? "—" : `${(x * 100).toFixed(digits)}%`;
