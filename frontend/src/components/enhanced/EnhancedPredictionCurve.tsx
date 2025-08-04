import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  Grid2,
} from '@mui/material';
import {
  TrendingUp,
  CenterFocusStrong,
  Timeline,
} from '@mui/icons-material';
import { PredictionResponse } from '../../types/api';

interface QuandMetrics {
  zScore: number;
  percentileRank: number;
  propToExpectedRatio: number;
  volatility: number;
  riskGrade: 'Low' | 'Moderate' | 'High' | 'Extreme';
  hitRate: number;
  volatilityTrend: 'Stable' | 'Increasing' | 'Decreasing';
}

interface EnhancedPredictionCurveProps {
  result: PredictionResponse;
  quantMetrics: QuandMetrics;
}

export const EnhancedPredictionCurve: React.FC<EnhancedPredictionCurveProps> = ({
  result,
  quantMetrics
}) => {
  const { expected_stat, prop_value, confidence } = result;
  
  // Calculate curve points for visualization
  const curvePoints = generateSensitivityCurve(expected_stat, prop_value, result.sample_details.volatility);
  const turningPoint = findTurningPoint(curvePoints);
  
  // Calculate prediction strength stability
  const strengthWindow = calculateStrengthWindow(curvePoints, prop_value);
  
  return (
    <Box>
      <Grid2 container spacing={3}>
        {/* Main Sensitivity Chart */}
        <Grid2 size={{ xs: 12, lg: 8 }}>
          <Box sx={{ position: 'relative', height: 200, mb: 3 }}>
            {/* Chart Background */}
            <Box sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'linear-gradient(180deg, rgba(76, 175, 80, 0.1) 0%, rgba(255, 193, 7, 0.1) 50%, rgba(244, 67, 54, 0.1) 100%)',
              borderRadius: 2,
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }} />
            
            {/* Confidence Curve Visualization */}
            <svg
              width="100%"
              height="100%"
              style={{ position: 'absolute', top: 0, left: 0 }}
              viewBox="0 0 400 200"
            >
              {/* Grid lines */}
              {[0, 25, 50, 75, 100].map(y => (
                <line
                  key={y}
                  x1="0"
                  y1={200 - (y * 2)}
                  x2="400"
                  y2={200 - (y * 2)}
                  stroke="rgba(255,255,255,0.1)"
                  strokeWidth="1"
                />
              ))}
              
              {/* Confidence curve */}
              <path
                d={generateCurvePath(curvePoints)}
                fill="none"
                stroke="#3f51b5"
                strokeWidth="3"
                strokeLinecap="round"
              />
              
              {/* Fill area under curve */}
              <path
                d={generateCurvePath(curvePoints) + " L400,200 L0,200 Z"}
                fill="rgba(63, 81, 181, 0.1)"
              />
              
              {/* Current prop value marker */}
              <line
                x1={getXPosition(prop_value, curvePoints)}
                y1="0"
                x2={getXPosition(prop_value, curvePoints)}
                y2="200"
                stroke="#f50057"
                strokeWidth="2"
                strokeDasharray="5,5"
              />
              
              {/* Expected stat marker */}
              <line
                x1={getXPosition(expected_stat, curvePoints)}
                y1="0"
                x2={getXPosition(expected_stat, curvePoints)}
                y2="200"
                stroke="#4caf50"
                strokeWidth="2"
              />
              
              {/* Turning point marker */}
              {turningPoint && (
                <circle
                  cx={getXPosition(turningPoint.prop_value, curvePoints)}
                  cy={200 - (turningPoint.confidence * 2)}
                  r="6"
                  fill="#ff9800"
                  stroke="#fff"
                  strokeWidth="2"
                />
              )}
            </svg>
            
            {/* Chart Labels */}
            <Box sx={{
              position: 'absolute',
              bottom: -40,
              left: 0,
              right: 0,
              display: 'flex',
              justifyContent: 'space-between',
              px: 2,
            }}>
              <Typography variant="caption" color="text.secondary">
                {curvePoints[0]?.prop_value.toFixed(1) || '0.0'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Prop Value Range
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {curvePoints[curvePoints.length - 1]?.prop_value.toFixed(1) || '10.0'}
              </Typography>
            </Box>
            
            {/* Y-axis labels */}
            <Box sx={{
              position: 'absolute',
              top: 0,
              left: -50,
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              py: 1,
            }}>
              <Typography variant="caption" color="text.secondary">100%</Typography>
              <Typography variant="caption" color="text.secondary">75%</Typography>
              <Typography variant="caption" color="text.secondary">50%</Typography>
              <Typography variant="caption" color="text.secondary">25%</Typography>
              <Typography variant="caption" color="text.secondary">0%</Typography>
            </Box>
          </Box>
          
          {/* Chart Legend */}
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Box sx={{ width: 16, height: 3, background: '#f50057', mr: 1 }} />
              <Typography variant="caption">Prop Line ({prop_value})</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Box sx={{ width: 16, height: 3, background: '#4caf50', mr: 1 }} />
              <Typography variant="caption">Expected ({expected_stat.toFixed(1)})</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Box sx={{ width: 16, height: 3, background: '#3f51b5', mr: 1 }} />
              <Typography variant="caption">Confidence Curve</Typography>
            </Box>
            {turningPoint && (
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Box sx={{ width: 12, height: 12, borderRadius: '50%', background: '#ff9800', mr: 1 }} />
                <Typography variant="caption">Turning Point</Typography>
              </Box>
            )}
          </Box>
        </Grid2>
        
        {/* Sensitivity Analysis Stats */}
        <Grid2 size={{ xs: 12, lg: 4 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, height: '100%' }}>
            {/* Turning Point Analysis */}
            <Paper sx={{
              p: 2,
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 2,
              flex: 1,
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CenterFocusStrong sx={{ mr: 1, color: 'warning.main', fontSize: 20 }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  Turning Point Analysis
                </Typography>
              </Box>
              {turningPoint ? (
                <>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Prediction flips at:
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 600, color: 'warning.main' }}>
                    {turningPoint.prop_value.toFixed(1)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {turningPoint.prediction} favored above this line
                  </Typography>
                </>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No turning point in analyzed range
                </Typography>
              )}
            </Paper>
            
            {/* Prediction Stability */}
            <Paper sx={{
              p: 2,
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 2,
              flex: 1,
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Timeline sx={{ mr: 1, color: 'info.main', fontSize: 20 }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  Prediction Strength
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Stability window:
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 600, color: 'info.main' }}>
                ±{strengthWindow.range.toFixed(1)}
              </Typography>
              <Chip
                label={strengthWindow.stability}
                size="small"
                color={strengthWindow.stability === 'Stable' ? 'success' : 
                       strengthWindow.stability === 'Moderate' ? 'warning' : 'error'}
                sx={{ mt: 1 }}
              />
            </Paper>
            
            {/* Sensitivity Metrics */}
            <Paper sx={{
              p: 2,
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 2,
              flex: 1,
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingUp sx={{ mr: 1, color: 'primary.main', fontSize: 20 }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  Sensitivity Metrics
                </Typography>
              </Box>
              <Box sx={{ mb: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Confidence at Prop:
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  {confidence}%
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Range Coverage:
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  {curvePoints.length} points analyzed
                </Typography>
              </Box>
            </Paper>
          </Box>
        </Grid2>
      </Grid2>
    </Box>
  );
};

// Helper functions for curve generation and analysis
function generateSensitivityCurve(expected_stat: number, prop_value: number, volatility: number) {
  const points = [];
  const range = Math.max(expected_stat * 0.8, 3); // Reasonable range around expected
  const start = Math.max(0.5, expected_stat - range);
  const end = expected_stat + range;
  const steps = 20;
  
  for (let i = 0; i <= steps; i++) {
    const currentProp = start + (end - start) * (i / steps);
    const distance = Math.abs(currentProp - expected_stat);
    const normalizedDistance = distance / (expected_stat * volatility);
    
    // Sigmoid function for realistic confidence curve
    const rawConfidence = 1 / (1 + Math.exp(normalizedDistance - 2));
    const confidence = Math.max(30, Math.min(95, rawConfidence * 100));
    
    const prediction = currentProp > expected_stat ? 'UNDER' : 'OVER';
    
    points.push({
      prop_value: currentProp,
      confidence: confidence,
      prediction: prediction as 'OVER' | 'UNDER',
      expected_stat: expected_stat,
      is_input_prop: Math.abs(currentProp - prop_value) < 0.1
    });
  }
  
  return points;
}

function findTurningPoint(curvePoints: any[]) {
  for (let i = 1; i < curvePoints.length; i++) {
    if (curvePoints[i].prediction !== curvePoints[i-1].prediction) {
      return curvePoints[i];
    }
  }
  return null;
}

function calculateStrengthWindow(curvePoints: any[], prop_value: number) {
  const currentPoint = curvePoints.find(p => Math.abs(p.prop_value - prop_value) < 0.2);
  if (!currentPoint) return { range: 0, stability: 'Unknown' };
  
  const baseConfidence = currentPoint.confidence;
  let leftRange = 0;
  let rightRange = 0;
  
  // Find how far confidence stays within 10% of current
  for (const point of curvePoints) {
    if (Math.abs(point.confidence - baseConfidence) <= 10) {
      if (point.prop_value < prop_value) {
        leftRange = Math.max(leftRange, prop_value - point.prop_value);
      } else if (point.prop_value > prop_value) {
        rightRange = Math.max(rightRange, point.prop_value - prop_value);
      }
    }
  }
  
  const totalRange = leftRange + rightRange;
  const stability = totalRange > 2 ? 'Stable' : totalRange > 1 ? 'Moderate' : 'Volatile';
  
  return { range: totalRange, stability };
}

function generateCurvePath(points: any[]): string {
  if (points.length === 0) return '';
  
  const pathCommands = points.map((point, index) => {
    const x = (index / (points.length - 1)) * 400;
    const y = 200 - (point.confidence * 2); // Scale confidence to chart height
    return index === 0 ? `M ${x} ${y}` : `L ${x} ${y}`;
  });
  
  return pathCommands.join(' ');
}

function getXPosition(value: number, points: any[]): number {
  if (points.length === 0) return 0;
  
  const minVal = points[0].prop_value;
  const maxVal = points[points.length - 1].prop_value;
  const normalizedPos = (value - minVal) / (maxVal - minVal);
  return normalizedPos * 400;
}