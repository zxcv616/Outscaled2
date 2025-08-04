import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  Grid2,
  LinearProgress,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Analytics,
  Assessment,
  Speed,
} from '@mui/icons-material';
import { PredictionResponse } from '../../types/api';

interface DeviationMetricsProps {
  result: PredictionResponse;
}

interface DeviationAnalysis {
  zScore: number;
  zScoreInterpretation: string;
  percentileRank: number;
  propToExpectedRatio: number;
  varianceRatio: number;
  deviationGrade: 'Minimal' | 'Low' | 'Moderate' | 'High' | 'Extreme';
  statisticalSignificance: 'None' | 'Weak' | 'Moderate' | 'Strong' | 'Very Strong';
}

const DeviationMetrics: React.FC<DeviationMetricsProps> = ({ result }) => {
  const analysis = calculateDeviationAnalysis(result);

  const getDeviationColor = (grade: string) => {
    switch (grade) {
      case 'Minimal': return 'success';
      case 'Low': return 'info';
      case 'Moderate': return 'warning';
      case 'High': return 'error';
      case 'Extreme': return 'error';
      default: return 'default';
    }
  };

  const getSignificanceColor = (significance: string) => {
    switch (significance) {
      case 'None': return 'default';
      case 'Weak': return 'info';
      case 'Moderate': return 'warning';
      case 'Strong': return 'success';
      case 'Very Strong': return 'success';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Grid2 container spacing={3}>
        {/* Z-Score Analysis */}
        <Grid2 size={{ xs: 12, md: 6 }}>
          <Paper sx={{ 
            p: 3, 
            background: 'rgba(255, 255, 255, 0.02)', 
            border: '1px solid rgba(255, 255, 255, 0.05)' 
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Speed sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Z-Score Analysis
              </Typography>
            </Box>
            
            <Box sx={{ textAlign: 'center', mb: 2 }}>
              <Typography variant="h3" sx={{ 
                fontWeight: 700, 
                color: analysis.zScore > 0 ? 'success.main' : 'error.main' 
              }}>
                {analysis.zScore > 0 ? '+' : ''}{analysis.zScore.toFixed(2)}σ
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Standard Deviations from Mean
              </Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Interpretation
              </Typography>
              <Typography variant="body1" sx={{ fontWeight: 500 }}>
                {analysis.zScoreInterpretation}
              </Typography>
            </Box>

            <Chip
              label={`Statistical Significance: ${analysis.statisticalSignificance}`}
              color={getSignificanceColor(analysis.statisticalSignificance) as any}
              size="small"
            />
          </Paper>
        </Grid2>

        {/* Percentile & Ratio Analysis */}
        <Grid2 size={{ xs: 12, md: 6 }}>
          <Paper sx={{ 
            p: 3, 
            background: 'rgba(255, 255, 255, 0.02)', 
            border: '1px solid rgba(255, 255, 255, 0.05)' 
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Assessment sx={{ mr: 1, color: 'secondary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Percentile Analysis
              </Typography>
            </Box>

            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Percentile Rank
                </Typography>
                <Typography variant="h5" sx={{ fontWeight: 600 }}>
                  {analysis.percentileRank}th
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={analysis.percentileRank}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: analysis.percentileRank > 75 ? '#4caf50' : 
                                   analysis.percentileRank > 50 ? '#ff9800' : '#f44336',
                  },
                }}
              />
            </Box>

            <Divider sx={{ mb: 2, borderColor: 'rgba(255, 255, 255, 0.1)' }} />

            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Prop/Expected Ratio
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {analysis.propToExpectedRatio.toFixed(3)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {analysis.propToExpectedRatio > 1 ? 'Above' : 'Below'} Expected
              </Typography>
            </Box>

            <Chip
              label={`Deviation Grade: ${analysis.deviationGrade}`}
              color={getDeviationColor(analysis.deviationGrade) as any}
              size="small"
            />
          </Paper>
        </Grid2>

        {/* Variance Analysis */}
        <Grid2 size={{ xs: 12 }}>
          <Paper sx={{ 
            p: 3, 
            background: 'rgba(255, 255, 255, 0.02)', 
            border: '1px solid rgba(255, 255, 255, 0.05)' 
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Analytics sx={{ mr: 1, color: 'info.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Variance Analysis
              </Typography>
            </Box>

            <Grid2 container spacing={2}>
              <Grid2 size={{ xs: 12, sm: 4 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'info.main' }}>
                    {analysis.varianceRatio.toFixed(2)}x
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Variance Ratio
                  </Typography>
                </Box>
              </Grid2>
              
              <Grid2 size={{ xs: 12, sm: 4 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
                    {Math.abs((result.expected_stat || 0) - (result.prop_value || 0)).toFixed(1)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Absolute Gap
                  </Typography>
                </Box>
              </Grid2>
              
              <Grid2 size={{ xs: 12, sm: 4 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'secondary.main' }}>
                    {result.sample_details?.maps_used || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Sample Size
                  </Typography>
                </Box>
              </Grid2>
            </Grid2>

            <Divider sx={{ my: 2, borderColor: 'rgba(255, 255, 255, 0.1)' }} />

            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                icon={analysis.zScore > 0 ? <TrendingUp /> : <TrendingDown />}
                label={`${Math.abs(analysis.zScore).toFixed(2)}σ ${analysis.zScore > 0 ? 'Above' : 'Below'}`}
                size="small"
                color={Math.abs(analysis.zScore) > 2 ? 'success' : 'default'}
                variant="outlined"
              />
              <Chip
                label={`${analysis.percentileRank}th Percentile`}
                size="small"
                color={analysis.percentileRank > 75 ? 'success' : analysis.percentileRank > 25 ? 'warning' : 'error'}
                variant="outlined"
              />
              <Chip
                label={`Ratio: ${analysis.propToExpectedRatio.toFixed(2)}`}
                size="small"
                color="info"
                variant="outlined"
              />
            </Box>
          </Paper>
        </Grid2>
      </Grid2>
    </Box>
  );
};

// Helper function to calculate comprehensive deviation analysis
function calculateDeviationAnalysis(result: PredictionResponse): DeviationAnalysis {
  const { expected_stat, prop_value, sample_details } = result;
  const volatility = sample_details?.volatility || 0.3; // Default volatility if not provided
  
  // Calculate Z-Score (standardized distance from mean) with null checks
  const safeExpectedStat = expected_stat || 0;
  const safePropValue = prop_value || 0;
  const safeVolatility = volatility || 0.3;
  
  let zScore = 0;
  if (safeExpectedStat !== 0 && safeVolatility !== 0) {
    const standardDeviation = safeExpectedStat * safeVolatility;
    if (standardDeviation !== 0) {
      zScore = (safePropValue - safeExpectedStat) / standardDeviation;
      // Validate z-score is a valid number
      if (isNaN(zScore) || !isFinite(zScore)) {
        zScore = 0;
      }
    }
  }
  
  // Interpret Z-Score
  const zScoreInterpretation = getZScoreInterpretation(zScore);
  
  // Calculate percentile rank (approximate)
  const percentileRank = calculatePercentileRank(safePropValue, safeExpectedStat, safeVolatility);
  
  // Calculate ratios with null checks
  const propToExpectedRatio = (safeExpectedStat !== 0) ? safePropValue / safeExpectedStat : 1;
  const varianceRatio = Math.pow(safeVolatility, 2) / Math.pow(0.25, 2); // Compared to baseline 25% volatility
  
  // Assign deviation grade
  const deviationGrade = getDeviationGrade(Math.abs(zScore));
  
  // Assign statistical significance
  const statisticalSignificance = getStatisticalSignificance(Math.abs(zScore));
  
  return {
    zScore,
    zScoreInterpretation,
    percentileRank,
    propToExpectedRatio,
    varianceRatio,
    deviationGrade,
    statisticalSignificance,
  };
}

function getZScoreInterpretation(zScore: number): string {
  const absZ = Math.abs(zScore);
  const direction = zScore > 0 ? 'above' : 'below';
  
  if (absZ < 0.5) return `Very close to expected value (within 0.5 standard deviations)`;
  if (absZ < 1.0) return `Moderately ${direction} expected (within 1 standard deviation)`;
  if (absZ < 2.0) return `Significantly ${direction} expected (1-2 standard deviations)`;
  if (absZ < 3.0) return `Highly ${direction} expected (2-3 standard deviations)`;
  return `Extremely ${direction} expected (>3 standard deviations)`;
}

function calculatePercentileRank(propValue: number, expectedStat: number, volatility: number): number {
  // Validate inputs
  if (!expectedStat || expectedStat === 0 || !volatility || volatility === 0) {
    return 50; // Default to median
  }
  
  // Approximate percentile calculation using normal distribution assumption
  const standardDeviation = expectedStat * volatility;
  if (standardDeviation === 0) {
    return 50;
  }
  
  const zScore = (propValue - expectedStat) / standardDeviation;
  
  // Validate z-score
  if (isNaN(zScore) || !isFinite(zScore)) {
    return 50;
  }
  
  // Convert Z-score to percentile (approximate)
  const percentile = 50 + (zScore * 34.13); // Rough approximation
  return Math.max(1, Math.min(99, Math.round(percentile)));
}

function getDeviationGrade(absZScore: number): 'Minimal' | 'Low' | 'Moderate' | 'High' | 'Extreme' {
  if (absZScore < 0.5) return 'Minimal';
  if (absZScore < 1.0) return 'Low';
  if (absZScore < 2.0) return 'Moderate';
  if (absZScore < 3.0) return 'High';
  return 'Extreme';
}

function getStatisticalSignificance(absZScore: number): 'None' | 'Weak' | 'Moderate' | 'Strong' | 'Very Strong' {
  if (absZScore < 1.0) return 'None';
  if (absZScore < 1.645) return 'Weak'; // 90% confidence
  if (absZScore < 1.96) return 'Moderate'; // 95% confidence
  if (absZScore < 2.58) return 'Strong'; // 99% confidence
  return 'Very Strong'; // 99.9% confidence
}

export default DeviationMetrics;