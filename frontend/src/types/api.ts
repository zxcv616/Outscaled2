export interface PredictionRequest {
  player_names: string[];
  prop_type: 'kills' | 'assists';
  prop_value: number;
  map_range: [number, number];
  opponent: string;
  tournament: string;
  team?: string;  // Now optional - backend will auto-infer if not provided
  match_date: string;
  position_roles: string[];
  strict_mode?: boolean;
}

export interface PlayerStats {
  avg_kills: number;
  avg_assists: number;
  form_z_score: number;
  maps_played: number;
  // position_factor: deprecated - now always 1.0, no longer a meaningful stat
  avg_deaths: number;
  avg_damage: number;
  avg_vision: number;
  avg_cs: number;
  // NEW: Enhanced stats from backend fixes
  series_played?: number;
  sample_size_score?: number;
  patch_recency_weight?: number;
}

export interface PredictionCurvePoint {
  prop_value: number;
  prediction: 'OVER' | 'UNDER';
  confidence: number;
  expected_stat: number;
  is_input_prop: boolean;
}

export interface TemporalCalibration {
  calibration_method: string;
  patch_awareness: boolean;
  needs_retraining: boolean;
  patch_group?: string;
  calibrated_confidence?: number;
  temporal_adjustment?: number;
  base_confidence_before_calibration?: number;
}

export interface SampleDetails {
  maps_used: number;
  filter_criteria: string;
  position: string;
  opponent: string;
  tournament: string;
  map_range: string;
  data_years: string;
  sample_quality: string;
  data_tier: number;
  tier_name: string;
  tier_weight: number;
  fallback_used: boolean;
  sample_sources: Record<string, number>;
  volatility: number;
  ci_method: string;
  strict_mode_applied: boolean;
  // NEW: Enhanced fields from backend fixes
  sample_size?: number;
  series_played?: number;
  data_quality?: string;
  patch_group?: string;
}

export interface PredictionResponse {
  prediction: 'OVER' | 'UNDER';
  confidence: number;
  base_model_confidence: number;
  data_tier: number;
  expected_stat: number;
  confidence_interval: [number, number];
  reasoning: string;
  player_stats: PlayerStats;
  data_years: string;
  sample_details: SampleDetails;
  confidence_warning: string;
  prediction_curve?: PredictionCurvePoint[];
  prop_type: 'kills' | 'assists';
  prop_value: number;
  // NEW: Enhanced fields from backend statistical fixes
  temporal_calibration?: TemporalCalibration;
}

export interface ApiError {
  detail?: string;
  message?: string;
  status_code?: number;
} 