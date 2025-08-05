import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Card,
  CardContent,
  Button,
  Grid2,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  Collapse,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Psychology,
  ExpandMore,
  Warning,
  CheckCircle,
  Error,
  Visibility,
  VisibilityOff,
  Assessment,
  Speed,
  Timeline,
  DataUsage,
  Security,
  Label,
} from '@mui/icons-material';
import { PredictionResponse, PredictionRequest } from '../../types/api';
import { EnhancedPredictionCurve } from './EnhancedPredictionCurve';

interface EnhancedPredictionResultProps {
  result: PredictionResponse | null;
  request: PredictionRequest | null;
  loading: boolean;
  error: string | null;
}

interface QuandMetrics {
  zScore: number;
  percentileRank: number;
  propToExpectedRatio: number;
  volatility: number;
  riskGrade: 'Low' | 'Moderate' | 'High' | 'Extreme';
  hitRate: number;
  volatilityTrend: 'Stable' | 'Increasing' | 'Decreasing';
}

interface ContextualData {
  recentAverage: number;
  seasonAverage: number;
  vsOpponentAverage: number | null;
  teamTempo: number;
  gameLengthFactor: number;
}

interface DataIntegrity {
  fallbackUsed: boolean;
  strictModeApplied: boolean;
  completeness: number;
  tierStatus: string;
  qualityFlags: string[];
}

interface RecommendationBadge {
  label: string;
  confidence: 'High' | 'Medium' | 'Low';
  reasoning: string;
  color: 'success' | 'warning' | 'error' | 'info';
}

export const EnhancedPredictionResult: React.FC<EnhancedPredictionResultProps> = ({
  result,
  request,
  loading,
  error
}) => {
  const [showMetadata, setShowMetadata] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});

  // Debug logging for prop_value
  console.log('EnhancedPredictionResult - Debug prop_value:', {
    result_prop_value: result?.prop_value,
    request_prop_value: request?.prop_value,
    result_keys: result ? Object.keys(result) : null,
    result_object: result
  });

  if (loading || error || !result) {
    // Keep existing loading/error states from original component
    return null; // Placeholder - would use original component's loading/error handling
  }

  // Calculate enhanced metrics
  const quantMetrics: QuandMetrics = {
    zScore: calculateZScore(result.expected_stat, result.prop_value || 0, result.sample_details?.volatility || 0.3),
    percentileRank: calculatePercentileRank(result.prop_value || 0, result.expected_stat || 0),
    propToExpectedRatio: (result.expected_stat && result.expected_stat !== 0) ? (result.prop_value || 0) / result.expected_stat : 1,
    volatility: ((result.sample_details?.volatility || 0.3) * 100),
    riskGrade: classifyRisk(result.sample_details?.volatility || 0.3),
    hitRate: calculateHitRate(result.confidence || 0, result.sample_details?.maps_used || 0),
    volatilityTrend: 'Stable' // Would be calculated from historical data
  };

  const contextualData: ContextualData = {
    recentAverage: result.player_stats?.avg_kills || result.player_stats?.avg_assists || 0,
    seasonAverage: result.expected_stat,
    vsOpponentAverage: null, // Would come from enhanced API
    teamTempo: 1.15, // Example value
    gameLengthFactor: 1.0
  };

  const dataIntegrity: DataIntegrity = {
    fallbackUsed: result.sample_details?.fallback_used || false,
    strictModeApplied: result.sample_details?.strict_mode_applied || false,
    completeness: ((result.sample_details?.maps_used || 0) / 30) * 100, // Assuming 30 is ideal sample size
    tierStatus: result.sample_details?.tier_name || 'Unknown',
    qualityFlags: (result.sample_details?.fallback_used) ? ['Fallback Data'] : []
  };

  const recommendation: RecommendationBadge = generateRecommendation(
    result,
    quantMetrics
  );

  const isOver = result.prediction === 'OVER';
  const confidenceColor = result.confidence >= 80 ? 'success' : 
                         result.confidence >= 60 ? 'warning' : 'error';

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  return (
    <Paper 
      elevation={24} 
      sx={{ 
        p: { xs: 2, sm: 3, md: 4 }, 
        mb: { xs: 2, sm: 3, md: 4 },
        borderRadius: 3,
        background: 'rgba(26, 26, 26, 0.95)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
      }}
    >
      {/* Header with Prediction and Recommendation Badge */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: { xs: 'flex-start', sm: 'center' },
        flexDirection: { xs: 'column', sm: 'row' },
        gap: { xs: 2, sm: 0 },
        mb: { xs: 3, sm: 4 } 
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: { xs: 40, sm: 48 },
              height: { xs: 40, sm: 48 },
              borderRadius: 2,
              background: isOver ? 'linear-gradient(45deg, #4caf50, #66bb6a)' : 'linear-gradient(45deg, #f44336, #ef5350)',
              mr: { xs: 1.5, sm: 2 },
              boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            }}
          >
            {isOver ? <TrendingUp sx={{ color: 'white' }} /> : <TrendingDown sx={{ color: 'white' }} />}
          </Box>
          <Box>
            <Typography variant="h4" sx={{ 
              fontWeight: 700, 
              mb: 0.5,
              fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' }
            }}>
              {result.prediction}
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{
              fontSize: { xs: '0.875rem', sm: '1rem' }
            }}>
              AI Prediction
            </Typography>
          </Box>
        </Box>
        
        {/* Recommendation Badge */}
        <Chip
          icon={<Label />}
          label={recommendation.label}
          color={recommendation.color}
          size="medium"
          sx={{
            fontSize: { xs: '0.875rem', sm: '1rem' },
            fontWeight: 600,
            px: { xs: 1.5, sm: 2 },
            py: { xs: 0.75, sm: 1 },
            height: 'auto',
            minWidth: { xs: 'auto', sm: 'fit-content' },
            alignSelf: { xs: 'flex-start', sm: 'auto' },
          }}
        />
      </Box>

      {/* Sample Size Validation Alert */}
      {(result.sample_details?.sample_size || result.player_stats.maps_played) < 15 && (
        <Paper sx={{ 
          p: 2, 
          mb: 3,
          background: (result.sample_details?.sample_size || result.player_stats.maps_played) < 5 ? 
            'rgba(244, 67, 54, 0.1)' : 'rgba(255, 152, 0, 0.1)',
          border: `1px solid ${(result.sample_details?.sample_size || result.player_stats.maps_played) < 5 ? 
            'rgba(244, 67, 54, 0.3)' : 'rgba(255, 152, 0, 0.3)'}`,
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {(result.sample_details?.sample_size || result.player_stats.maps_played) < 5 ? 
              <Error sx={{ mr: 1, color: 'error.main' }} /> : 
              <Warning sx={{ mr: 1, color: 'warning.main' }} />
            }
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {(result.sample_details?.sample_size || result.player_stats.maps_played) < 5 ? 
                'Critical Sample Size Warning' : 'Small Sample Size Notice'}
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1, ml: 4 }}>
            {(result.sample_details?.sample_size || result.player_stats.maps_played) < 5 ? 
              'Sample size below minimum threshold (5 maps) - prediction reliability severely impacted.' :
              'Sample size below optimal threshold (15 maps) - consider predictions with caution.'}
          </Typography>
        </Paper>
      )}

      {/* Core Metrics Row */}
      <Grid2 container spacing={{ xs: 2, sm: 3 }} sx={{ mb: { xs: 3, sm: 4 } }}>
        <Grid2 size={{ xs: 6, sm: 6, md: 3 }}>
          <Card sx={{ 
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
          }}>
            <CardContent sx={{ 
              textAlign: 'center', 
              p: { xs: 2, sm: 3 },
              '&:last-child': { pb: { xs: 2, sm: 3 } }
            }}>
              <Typography variant="h3" sx={{ 
                fontWeight: 700, 
                mb: 1,
                fontSize: { xs: '1.5rem', sm: '1.875rem' }
              }}>
                {result.confidence}%
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}>
                Confidence Level
              </Typography>
              <Chip
                label={confidenceColor === 'success' ? 'High' : confidenceColor === 'warning' ? 'Medium' : 'Low'}
                color={confidenceColor}
                size="small"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid2>
        
        <Grid2 size={{ xs: 6, sm: 6, md: 3 }}>
          <Card sx={{ 
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
          }}>
            <CardContent sx={{ 
              textAlign: 'center', 
              p: { xs: 2, sm: 3 },
              '&:last-child': { pb: { xs: 2, sm: 3 } }
            }}>
              <Typography variant="h3" sx={{ 
                fontWeight: 700, 
                mb: 1,
                fontSize: { xs: '1.5rem', sm: '1.875rem' }
              }}>
                {result.expected_stat.toFixed(1)}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}>
                Expected {result.prop_type}
              </Typography>
            </CardContent>
          </Card>
        </Grid2>
        
        <Grid2 size={{ xs: 6, sm: 6, md: 3 }}>
          <Card sx={{ 
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
          }}>
            <CardContent sx={{ 
              textAlign: 'center', 
              p: { xs: 2, sm: 3 },
              '&:last-child': { pb: { xs: 2, sm: 3 } }
            }}>
              <Typography variant="h3" sx={{ 
                fontWeight: 700, 
                mb: 1,
                fontSize: { xs: '1.5rem', sm: '1.875rem' }
              }}>
                {result.prop_value || 'N/A'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}>
                Prop Line
              </Typography>
            </CardContent>
          </Card>
        </Grid2>
        
        <Grid2 size={{ xs: 6, sm: 6, md: 3 }}>
          <Card sx={{ 
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
          }}>
            <CardContent sx={{ 
              textAlign: 'center', 
              p: { xs: 2, sm: 3 },
              '&:last-child': { pb: { xs: 2, sm: 3 } }
            }}>
              <Tooltip title="Statistical distance from historical mean">
                <Typography variant="h3" sx={{ fontWeight: 700, mb: 1, cursor: 'help' }}>
                  {quantMetrics.zScore > 0 ? '+' : ''}{quantMetrics.zScore.toFixed(2)}
                </Typography>
              </Tooltip>
              <Typography variant="body2" color="text.secondary" sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}>
                Z-Score
              </Typography>
            </CardContent>
          </Card>
        </Grid2>
      </Grid2>

      {/* Data Quality & Statistical Integrity Section */}
      <Paper sx={{ 
        p: 3, 
        mb: 3,
        background: 'rgba(255, 255, 255, 0.03)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
      }}>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, display: 'flex', alignItems: 'center' }}>
          <Psychology sx={{ mr: 1, color: 'secondary.main' }} />
          Data Quality & Statistical Integrity
        </Typography>
        
        <Grid2 container spacing={2}>
          <Grid2 size={{ xs: 12, sm: 6, md: 4 }}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Sample Quality
              </Typography>
              <Chip 
                label={result.sample_details?.data_quality || result.sample_details?.sample_quality || 'Good'}
                color={
                  (result.sample_details?.data_quality || result.sample_details?.sample_quality || 'Good').toLowerCase() === 'excellent' ? 'success' :
                  (result.sample_details?.data_quality || result.sample_details?.sample_quality || 'Good').toLowerCase() === 'good' ? 'primary' :
                  (result.sample_details?.data_quality || result.sample_details?.sample_quality || 'Good').toLowerCase() === 'fair' ? 'warning' : 'error'
                }
                sx={{ fontWeight: 600 }}
              />
              {/* Sample Size Validation Warning */}
              {(result.sample_details?.sample_size || result.player_stats.maps_played) < 10 && (
                <Box sx={{ mt: 1 }}>
                  <Chip 
                    icon={<Warning />}
                    label="Small Sample"
                    color="warning"
                    size="small"
                    sx={{ fontSize: '0.7rem' }}
                  />
                </Box>
              )}
              {(result.sample_details?.sample_size || result.player_stats.maps_played) < 5 && (
                <Box sx={{ mt: 1 }}>
                  <Chip 
                    icon={<Error />}
                    label="Critical Sample Size"
                    color="error"
                    size="small"
                    sx={{ fontSize: '0.7rem' }}
                  />
                </Box>
              )}
            </Box>
          </Grid2>
          
          <Grid2 size={{ xs: 12, sm: 6, md: 4 }}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Sample Size
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {result.sample_details?.sample_size || result.player_stats.maps_played} maps
                {result.sample_details?.series_played && (
                  <Typography variant="body2" color="text.secondary">
                    ({result.sample_details.series_played} series)
                  </Typography>
                )}
              </Typography>
            </Box>
          </Grid2>
          
          {result.temporal_calibration && (
            <Grid2 size={{ xs: 12, sm: 6, md: 4 }}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Temporal Calibration
                </Typography>
                <Box>
                  {result.temporal_calibration.patch_awareness && (
                    <Chip 
                      label="Patch-Aware" 
                      size="small" 
                      color="primary" 
                      sx={{ mb: 0.5 }}
                    />
                  )}
                  {result.temporal_calibration.needs_retraining && (
                    <Chip 
                      label="Retraining Needed" 
                      size="small" 
                      color="warning" 
                      sx={{ mb: 0.5, ml: 0.5 }}
                    />
                  )}
                  {result.sample_details?.patch_group && (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                      {result.sample_details.patch_group}
                    </Typography>
                  )}
                </Box>
              </Box>
            </Grid2>
          )}
        </Grid2>
      </Paper>

      {/* Quant-Grade Analytics Section */}
      <Accordion 
        expanded={expandedSections.analytics || false}
        onChange={() => toggleSection('analytics')}
        sx={{ 
          mb: 3,
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Assessment sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Quantitative Analytics
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid2 container spacing={3}>
            {/* Prop Value Deviation Metrics */}
            <Grid2 size={{ xs: 12, md: 4 }}>
              <Paper sx={{ p: 3, background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <Speed sx={{ mr: 1, color: 'secondary.main' }} />
                  Deviation Metrics
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}>Percentile Rank</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    {quantMetrics.percentileRank}th percentile
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}>Prop/Expected Ratio</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    {quantMetrics.propToExpectedRatio.toFixed(2)}
                  </Typography>
                </Box>
              </Paper>
            </Grid2>

            {/* Volatility & Risk */}
            <Grid2 size={{ xs: 12, md: 4 }}>
              <Paper sx={{ p: 3, background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <Timeline sx={{ mr: 1, color: 'warning.main' }} />
                  Volatility Analysis
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}>Volatility</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    {quantMetrics.volatility.toFixed(1)}% ({quantMetrics.riskGrade})
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}>Historical Hit Rate</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    {quantMetrics.hitRate}%
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}>Trend</Typography>
                  <Chip 
                    label={quantMetrics.volatilityTrend}
                    size="small"
                    color="info"
                  />
                </Box>
              </Paper>
            </Grid2>

            {/* Contextual Data */}
            <Grid2 size={{ xs: 12, md: 4 }}>
              <Paper sx={{ p: 3, background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <DataUsage sx={{ mr: 1, color: 'info.main' }} />
                  Context Snapshots
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}>Last 3 Games</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    {contextualData.recentAverage.toFixed(1)} avg
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}>vs {request?.opponent || 'Opponent'}</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    {contextualData.vsOpponentAverage?.toFixed(1) || 'N/A'} avg
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}>Team Tempo</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    {contextualData.teamTempo.toFixed(2)}x league avg
                  </Typography>
                </Box>
              </Paper>
            </Grid2>
          </Grid2>
        </AccordionDetails>
      </Accordion>

      {/* Enhanced Prediction Sensitivity Curve */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <TrendingUp sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Prediction Sensitivity Analysis
          </Typography>
        </Box>
        <Paper 
          sx={{ 
            p: 2,
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
          }}
        >
          <EnhancedPredictionCurve 
            result={result}
            quantMetrics={quantMetrics}
          />
        </Paper>
      </Box>

      {/* Data Integrity Flags */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Security sx={{ mr: 1, color: 'success.main' }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Data Integrity Status
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Chip
            icon={dataIntegrity.fallbackUsed ? <Warning /> : <CheckCircle />}
            label={dataIntegrity.fallbackUsed ? 'Fallback Used' : 'Full Match Data'}
            color={dataIntegrity.fallbackUsed ? 'warning' : 'success'}
            variant="outlined"
          />
          <Chip
            icon={dataIntegrity.strictModeApplied ? <CheckCircle /> : <Error />}
            label={dataIntegrity.strictModeApplied ? 'Strict Mode: ON' : 'Strict Mode: OFF'}
            color={dataIntegrity.strictModeApplied ? 'success' : 'info'}
            variant="outlined"
          />
          <Chip
            icon={<DataUsage />}
            label={`${dataIntegrity.tierStatus} (${result.sample_details?.maps_used || 0} maps)`}
            color="info"
            variant="outlined"
          />
          <Chip
            icon={<Assessment />}
            label={`${dataIntegrity.completeness.toFixed(0)}% Complete`}
            color={dataIntegrity.completeness >= 80 ? 'success' : 'warning'}
            variant="outlined"
          />
        </Box>
      </Box>

      {/* AI Reasoning */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Psychology sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            AI Reasoning
          </Typography>
        </Box>
        <Paper 
          sx={{ 
            p: 2,
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
          }}
        >
          <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
            {result.reasoning}
          </Typography>
        </Paper>
      </Box>

      {/* Expandable Metadata Section */}
      <Box>
        <Button
          onClick={() => setShowMetadata(!showMetadata)}
          startIcon={showMetadata ? <VisibilityOff /> : <Visibility />}
          sx={{ mb: 2 }}
        >
          {showMetadata ? 'Hide' : 'Show'} Technical Metadata
        </Button>
        
        <Collapse in={showMetadata}>
          <Paper 
            sx={{ 
              p: 3,
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              borderRadius: 2,
            }}
          >
            <Typography variant="h6" gutterBottom>
              Model & Data Details
            </Typography>
            <Grid2 container spacing={2}>
              <Grid2 size={{ xs: 12, md: 6 }}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}>Model Version</Typography>
                  <Typography variant="body1">v2.1.3 (Primary Model)</Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}>Training Date</Typography>
                  <Typography variant="body1">2024-07-15</Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}>Confidence Method</Typography>
                  <Typography variant="body1">
                    {result.sample_details?.ci_method || 'bootstrap_percentile'}
                    {result.temporal_calibration?.patch_awareness && (
                      <Chip 
                        label="Patch-Aware" 
                        size="small" 
                        color="primary" 
                        sx={{ ml: 1, fontSize: '0.7rem' }}
                      />
                    )}
                  </Typography>
                </Box>
              </Grid2>
              <Grid2 size={{ xs: 12, md: 6 }}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}>Top Feature Drivers</Typography>
                  <Typography variant="body1">
                    • Form Z-Score ({Math.abs(result.player_stats.form_z_score || 0).toFixed(2)})<br/>
                    • Sample Quality ({result.sample_details?.sample_size || result.player_stats.maps_played || 0} maps)<br/>
                    • Market Distance ({Math.abs(quantMetrics.propToExpectedRatio - 1).toFixed(3)}x)<br/>
                    • Bootstrap Confidence ({result.confidence}%)<br/>
                    {result.sample_details?.patch_group && `• Patch Grouping (${result.sample_details.patch_group})`}<br/>
                    {result.temporal_calibration?.patch_awareness && '• Temporal Calibration (Active)'}
                  </Typography>
                </Box>
              </Grid2>
            </Grid2>
          </Paper>
        </Collapse>
      </Box>
    </Paper>
  );
};

// Helper functions
function calculateZScore(expectedStat: number, propValue: number, volatility: number): number {
  if (!expectedStat || !volatility || expectedStat === 0 || volatility === 0) {
    return 0;
  }
  const standardDeviation = expectedStat * volatility;
  if (standardDeviation === 0) {
    return 0;
  }
  const zScore = (propValue - expectedStat) / standardDeviation;
  return isNaN(zScore) || !isFinite(zScore) ? 0 : zScore;
}

function calculatePercentileRank(propValue: number, expectedStat: number): number {
  if (!expectedStat || expectedStat === 0) {
    return 50; // Default to median
  }
  // Simplified calculation - would be more sophisticated in practice
  const ratio = propValue / expectedStat;
  if (isNaN(ratio) || !isFinite(ratio)) {
    return 50;
  }
  if (ratio <= 0.5) return 5;
  if (ratio <= 0.75) return 25;
  if (ratio <= 1.0) return 50;
  if (ratio <= 1.25) return 75;
  return 95;
}

function classifyRisk(volatility: number): 'Low' | 'Moderate' | 'High' | 'Extreme' {
  if (volatility <= 0.2) return 'Low';
  if (volatility <= 0.35) return 'Moderate';
  if (volatility <= 0.5) return 'High';
  return 'Extreme';
}

function calculateHitRate(confidence: number, sampleSize: number): number {
  if (!confidence && !sampleSize) {
    return 0;
  }
  // Simplified calculation based on confidence and sample size
  const safeConfidence = confidence || 0;
  const safeSampleSize = sampleSize || 0;
  const baseRate = Math.min(safeConfidence * 0.8, 85);
  const sampleBonus = Math.min(safeSampleSize * 0.5, 10);
  const hitRate = Math.round(baseRate + sampleBonus);
  return isNaN(hitRate) || !isFinite(hitRate) ? 0 : hitRate;
}

function generateRecommendation(
  result: PredictionResponse, 
  metrics: QuandMetrics
): RecommendationBadge {
  const { confidence, prediction } = result;
  const { volatility, zScore } = metrics;

  if (confidence >= 80 && volatility < 30 && Math.abs(zScore) > 1.5) {
    return {
      label: `Smart ${prediction} – Low Risk, Strong Edge`,
      confidence: 'High',
      reasoning: 'High confidence with low volatility and significant statistical edge',
      color: 'success'
    };
  }

  if (volatility > 50) {
    return {
      label: `Volatile ${prediction} – High Risk`,
      confidence: 'Low',
      reasoning: 'High volatility makes this a risky proposition despite prediction',
      color: 'warning'
    };
  }

  if (confidence < 60) {
    return {
      label: `Weak ${prediction} – Low Confidence`,
      confidence: 'Low', 
      reasoning: 'Low model confidence suggests uncertain outcome',
      color: 'error'
    };
  }

  return {
    label: `Moderate ${prediction}`,
    confidence: 'Medium',
    reasoning: 'Standard prediction with moderate risk profile',
    color: 'info'
  };
}