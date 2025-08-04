import React from 'react';
import {
  Box,
  Typography,
  Chip,
  Paper,
  Grid2,
} from '@mui/material';
import {
  ThumbUp,
  ThumbDown,
  Warning,
  Stars,
  TrendingUp,
  Security,
} from '@mui/icons-material';
import { PredictionResponse } from '../../types/api';

interface RecommendationBadgesProps {
  result: PredictionResponse;
}

interface Recommendation {
  badge: string;
  confidence: 'High' | 'Medium' | 'Low';
  reasoning: string;
  color: 'success' | 'warning' | 'error' | 'info';
  icon: React.ReactElement;
  actionable: boolean;
}

const RecommendationBadges: React.FC<RecommendationBadgesProps> = ({ result }) => {
  const recommendations = generateRecommendations(result);

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Stars sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          AI Recommendations
        </Typography>
      </Box>

      <Grid2 container spacing={2}>
        {recommendations.map((rec, index) => (
          <Grid2 key={index} size={{ xs: 12, sm: 6, md: 4 }}>
            <Paper sx={{
              p: 2,
              background: 'rgba(255, 255, 255, 0.02)',
              border: `1px solid rgba(${
                rec.color === 'success' ? '76, 175, 80' :
                rec.color === 'warning' ? '255, 152, 0' :
                rec.color === 'error' ? '244, 67, 54' : '63, 81, 181'
              }, 0.3)`,
              borderRadius: 2,
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Box sx={{ mr: 1, color: `${rec.color}.main` }}>
                  {rec.icon}
                </Box>
                <Chip
                  label={rec.badge}
                  color={rec.color}
                  size="small"
                  sx={{ fontWeight: 600 }}
                />
              </Box>

              <Box sx={{ flex: 1, mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  {rec.reasoning}
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Chip
                  label={`${rec.confidence} Confidence`}
                  size="small"
                  variant="outlined"
                  color={rec.confidence === 'High' ? 'success' : rec.confidence === 'Medium' ? 'warning' : 'error'}
                />
                {rec.actionable && (
                  <Chip
                    label="Actionable"
                    size="small"
                    color="info"
                    variant="filled"
                  />
                )}
              </Box>
            </Paper>
          </Grid2>
        ))}
      </Grid2>
    </Box>
  );
};

function generateRecommendations(result: PredictionResponse): Recommendation[] {
  const recommendations: Recommendation[] = [];
  const { confidence, expected_stat, prop_value, sample_details, prediction } = result;
  const volatility = sample_details?.volatility || 0.3;
  const sampleSize = sample_details?.maps_used || 0;
  const gap = Math.abs(expected_stat - prop_value);

  // Primary recommendation based on overall strength
  if (confidence >= 80 && volatility < 0.3 && sampleSize >= 15) {
    recommendations.push({
      badge: `Strong ${prediction} - High Value`,
      confidence: 'High',
      reasoning: 'High confidence with low volatility and strong sample size. This appears to be a high-quality prediction.',
      color: 'success',
      icon: <ThumbUp />,
      actionable: true
    });
  } else if (confidence >= 70 && volatility < 0.4) {
    recommendations.push({
      badge: `Moderate ${prediction} - Good Value`,
      confidence: 'Medium',
      reasoning: 'Decent confidence with acceptable volatility. Consider for standard betting strategies.',
      color: 'info',
      icon: <TrendingUp />,
      actionable: true
    });
  } else if (confidence < 60 || volatility > 0.5) {
    recommendations.push({
      badge: `Weak ${prediction} - Avoid`,
      confidence: 'Low',
      reasoning: 'Low confidence or high volatility makes this a risky proposition. Consider avoiding.',
      color: 'error',
      icon: <ThumbDown />,
      actionable: false
    });
  }

  // Edge-based recommendation
  const edgePercentage = (gap / prop_value) * 100;
  if (edgePercentage > 15) {
    recommendations.push({
      badge: 'Significant Edge Detected',
      confidence: 'High',
      reasoning: `Large gap of ${gap.toFixed(1)} between prop and expected creates substantial edge opportunity.`,
      color: 'success',
      icon: <Stars />,
      actionable: true
    });
  } else if (edgePercentage > 8) {
    recommendations.push({
      badge: 'Moderate Edge Available',
      confidence: 'Medium',
      reasoning: `Gap of ${gap.toFixed(1)} provides decent edge for value betting strategies.`,
      color: 'warning',
      icon: <TrendingUp />,
      actionable: true
    });
  }

  // Sample size warning
  if (sampleSize < 10) {
    recommendations.push({
      badge: 'Limited Data Warning',
      confidence: 'Low',
      reasoning: `Small sample size (${sampleSize} maps) increases prediction uncertainty. Use caution.`,
      color: 'warning',
      icon: <Warning />,
      actionable: false
    });
  }

  // Volatility-based recommendation
  if (volatility > 0.4) {
    recommendations.push({
      badge: 'High Volatility Alert',
      confidence: 'Medium',
      reasoning: `High volatility (${(volatility * 100).toFixed(0)}%) suggests unpredictable performance. Consider smaller positions.`,
      color: 'warning',
      icon: <Warning />,
      actionable: false
    });
  } else if (volatility < 0.2) {
    recommendations.push({
      badge: 'Stable Performance',
      confidence: 'High',
      reasoning: `Low volatility (${(volatility * 100).toFixed(0)}%) indicates consistent performance pattern.`,
      color: 'success',
      icon: <Security />,
      actionable: true
    });
  }

  // Fallback data warning
  if (sample_details?.fallback_used) {
    recommendations.push({
      badge: 'Fallback Data Used',
      confidence: 'Low',
      reasoning: 'Prediction uses fallback data due to insufficient direct match data. Reliability reduced.',
      color: 'warning',
      icon: <Warning />,
      actionable: false
    });
  }

  return recommendations;
}

export default RecommendationBadges;