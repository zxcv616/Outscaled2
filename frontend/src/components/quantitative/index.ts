// Quantitative Analysis Components
// Professional-grade components for quantitative analysts

export { default as DeviationMetrics } from './DeviationMetrics';
export { default as VolatilityRiskClassification } from './VolatilityRiskClassification';
export { default as SensitivityCurve } from './SensitivityCurve';
export { default as ContextualDataSnapshot } from './ContextualDataSnapshot';
export { default as DataIntegrityFlags } from './DataIntegrityFlags';
export { default as RecommendationBadges } from './RecommendationBadges';
export { default as ExpandableMetadata } from './ExpandableMetadata';

// Component descriptions for documentation
export const COMPONENT_DESCRIPTIONS = {
  DeviationMetrics: 'Statistical deviation analysis with Z-scores, percentiles, and variance ratios',
  VolatilityRiskClassification: 'Risk assessment with volatility scoring and management recommendations',
  SensitivityCurve: 'Interactive sensitivity analysis showing prediction response to prop changes',
  ContextualDataSnapshot: 'Comprehensive contextual information about data sources and quality',
  DataIntegrityFlags: 'Data quality flags and warnings with impact assessments',
  RecommendationBadges: 'AI-generated betting recommendations with confidence tiers',
  ExpandableMetadata: 'Detailed technical metadata and debugging information'
} as const;