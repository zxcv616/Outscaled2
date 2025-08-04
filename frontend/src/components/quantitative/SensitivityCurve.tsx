import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  Grid2,
  Tooltip,
} from '@mui/material';
import {
  TrendingUp,
  CenterFocusStrong,
  Timeline,
  ShowChart,
} from '@mui/icons-material';
import { PredictionResponse } from '../../types/api';

interface SensitivityCurveProps {
  result: PredictionResponse;
}

interface SensitivityPoint {
  propValue: number;
  confidence: number;
  prediction: 'OVER' | 'UNDER';
  isOptimal: boolean;
  riskLevel: 'Low' | 'Medium' | 'High';
}

interface SensitivityAnalysis {
  points: SensitivityPoint[];
  turningPoint: SensitivityPoint | null;
  optimalRange: { min: number; max: number };
  stability: 'Stable' | 'Moderate' | 'Volatile';
  maxConfidence: number;
  minConfidence: number;
}

const SensitivityCurve: React.FC<SensitivityCurveProps> = ({ result }) => {
  const analysis = generateSensitivityAnalysis(result);

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'Low': return '#4caf50';
      case 'Medium': return '#ff9800';
      case 'High': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  const getStabilityColor = (stability: string) => {
    switch (stability) {
      case 'Stable': return 'success';
      case 'Moderate': return 'warning';
      case 'Volatile': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Grid2 container spacing={3}>
        {/* Main Sensitivity Chart */}
        <Grid2 size={{ xs: 12, lg: 8 }}>
          <Box sx={{ position: 'relative', height: 250, mb: 3 }}>
            {/* Chart Background with Gradient */}
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
            
            {/* SVG Chart */}
            <svg
              width="100%"
              height="100%"
              style={{ position: 'absolute', top: 0, left: 0 }}
              viewBox="0 0 500 250"
            >
              {/* Grid lines */}
              {[0, 25, 50, 75, 100].map(y => (
                <line
                  key={`grid-${y}`}
                  x1="50"
                  y1={225 - (y * 1.75)}
                  x2="450"
                  y2={225 - (y * 1.75)}
                  stroke="rgba(255,255,255,0.1)"
                  strokeWidth="1"
                />
              ))}
              
              {/* Vertical grid lines */}
              {[0, 25, 50, 75, 100].map(x => (
                <line
                  key={`vgrid-${x}`}
                  x1={50 + (x * 4)}
                  y1="25"
                  x2={50 + (x * 4)}
                  y2="225"
                  stroke="rgba(255,255,255,0.05)"
                  strokeWidth="1"
                />
              ))}
              
              {/* Confidence curve */}
              <path
                d={generateCurvePath(analysis.points)}
                fill="none"
                stroke="#3f51b5"
                strokeWidth="3"
                strokeLinecap="round"
              />
              
              {/* Fill area under curve */}
              <path
                d={generateCurvePath(analysis.points) + " L450,225 L50,225 Z"}
                fill="rgba(63, 81, 181, 0.1)"
              />
              
              {/* Risk level indicators */}
              {analysis.points.map((point, index) => {
                if (index % 3 !== 0) return null; // Show every 3rd point to avoid clutter
                const x = 50 + ((point.propValue - analysis.points[0].propValue) / 
                  (analysis.points[analysis.points.length - 1].propValue - analysis.points[0].propValue)) * 400;
                const y = 225 - (point.confidence * 1.75);
                
                return (
                  <circle
                    key={`point-${index}`}
                    cx={x}
                    cy={y}
                    r="3"
                    fill={getRiskColor(point.riskLevel)}
                    stroke="#fff"
                    strokeWidth="1"
                  />
                );
              })}
              
              {/* Current prop value marker */}
              <line
                x1={getCurrentPropX(result.prop_value, analysis.points)}
                y1="25"
                x2={getCurrentPropX(result.prop_value, analysis.points)}
                y2="225"
                stroke="#f50057"
                strokeWidth="3"
                strokeDasharray="5,5"
              />
              
              {/* Turning point marker */}
              {analysis.turningPoint && (
                <g>
                  <circle
                    cx={getCurrentPropX(analysis.turningPoint.propValue, analysis.points)}
                    cy={225 - (analysis.turningPoint.confidence * 1.75)}
                    r="8"
                    fill="#ff9800"
                    stroke="#fff"
                    strokeWidth="2"
                  />
                  <text
                    x={getCurrentPropX(analysis.turningPoint.propValue, analysis.points)}
                    y={225 - (analysis.turningPoint.confidence * 1.75) - 15}
                    textAnchor="middle"
                    fill="#ff9800"
                    fontSize="10"
                    fontWeight="bold"
                  >
                    Turning Point
                  </text>
                </g>
              )}
              
              {/* Y-axis labels */}
              <text x="25" y="30" fill="#fff" fontSize="10" textAnchor="middle">100%</text>
              <text x="25" y="75" fill="#fff" fontSize="10" textAnchor="middle">75%</text>
              <text x="25" y="130" fill="#fff" fontSize="10" textAnchor="middle">50%</text>
              <text x="25" y="180" fill="#fff" fontSize="10" textAnchor="middle">25%</text>
              <text x="25" y="230" fill="#fff" fontSize="10" textAnchor="middle">0%</text>
              
              {/* X-axis labels */}
              <text x="50" y="245" fill="#fff" fontSize="10" textAnchor="middle">
                {analysis.points[0]?.propValue.toFixed(1)}
              </text>
              <text x="250" y="245" fill="#fff" fontSize="10" textAnchor="middle">
                Prop Value
              </text>
              <text x="450" y="245" fill="#fff" fontSize="10" textAnchor="middle">
                {analysis.points[analysis.points.length - 1]?.propValue.toFixed(1)}
              </text>
            </svg>
          </Box>
          
          {/* Chart Legend */}
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Box sx={{ width: 16, height: 3, background: '#f50057', mr: 1 }} />
              <Typography variant="caption">Current Prop ({result.prop_value})</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Box sx={{ width: 16, height: 3, background: '#3f51b5', mr: 1 }} />
              <Typography variant="caption">Confidence Curve</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Box sx={{ width: 12, height: 12, borderRadius: '50%', background: '#4caf50', mr: 1 }} />
              <Typography variant="caption">Low Risk</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Box sx={{ width: 12, height: 12, borderRadius: '50%', background: '#ff9800', mr: 1 }} />
              <Typography variant="caption">Medium Risk</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Box sx={{ width: 12, height: 12, borderRadius: '50%', background: '#f44336', mr: 1 }} />
              <Typography variant="caption">High Risk</Typography>
            </Box>
          </Box>
        </Grid2>
        
        {/* Analysis Stats */}
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
                  Turning Point
                </Typography>
              </Box>
              {analysis.turningPoint ? (
                <>
                  <Typography variant="h5" sx={{ fontWeight: 600, color: 'warning.main', mb: 1 }}>
                    {analysis.turningPoint.propValue.toFixed(1)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Prediction flips to {analysis.turningPoint.prediction}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Confidence: {analysis.turningPoint.confidence.toFixed(1)}%
                  </Typography>
                </>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No turning point in range
                </Typography>
              )}
            </Paper>
            
            {/* Stability Analysis */}
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
                  Stability Analysis
                </Typography>
              </Box>
              <Chip
                label={analysis.stability}
                size="small"
                color={getStabilityColor(analysis.stability) as any}
                sx={{ mb: 2 }}
              />
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Optimal Range:
              </Typography>
              <Typography variant="body1" sx={{ fontWeight: 600 }}>
                {analysis.optimalRange.min.toFixed(1)} - {analysis.optimalRange.max.toFixed(1)}
              </Typography>
            </Paper>
            
            {/* Confidence Range */}
            <Paper sx={{
              p: 2,
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 2,
              flex: 1,
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ShowChart sx={{ mr: 1, color: 'primary.main', fontSize: 20 }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  Confidence Range
                </Typography>
              </Box>
              <Box sx={{ mb: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Maximum:
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 600, color: 'success.main' }}>
                  {analysis.maxConfidence.toFixed(1)}%
                </Typography>
              </Box>
              <Box sx={{ mb: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Minimum:
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 600, color: 'error.main' }}>
                  {analysis.minConfidence.toFixed(1)}%
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Current:
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 600, color: 'primary.main' }}>
                  {result.confidence}%
                </Typography>
              </Box>
            </Paper>
          </Box>
        </Grid2>
      </Grid2>
    </Box>
  );
};

// Helper functions
function generateSensitivityAnalysis(result: PredictionResponse): SensitivityAnalysis {
  const { expected_stat, prop_value, sample_details } = result;
  const volatility = sample_details?.volatility || 0.3;
  
  // Generate sensitivity curve points
  const points: SensitivityPoint[] = [];
  const range = Math.max(expected_stat * 0.6, 3);
  const start = Math.max(0.5, expected_stat - range);
  const end = expected_stat + range;
  const steps = 25;
  
  for (let i = 0; i <= steps; i++) {
    const currentProp = start + (end - start) * (i / steps);
    const distance = Math.abs(currentProp - expected_stat);
    const normalizedDistance = distance / (expected_stat * volatility);
    
    // Sigmoid function for realistic confidence curve
    const rawConfidence = 1 / (1 + Math.exp(normalizedDistance - 1.5));
    const confidence = Math.max(25, Math.min(95, rawConfidence * 100));
    
    const prediction: 'OVER' | 'UNDER' = currentProp > expected_stat ? 'UNDER' : 'OVER';
    const riskLevel = getRiskLevel(distance, expected_stat, volatility);
    const isOptimal = confidence > 70 && riskLevel === 'Low';
    
    points.push({
      propValue: currentProp,
      confidence,
      prediction,
      isOptimal,
      riskLevel,
    });
  }
  
  // Find turning point
  const turningPoint = findTurningPoint(points);
  
  // Calculate optimal range
  const optimalPoints = points.filter(p => p.isOptimal);
  const optimalRange = {
    min: optimalPoints.length > 0 ? Math.min(...optimalPoints.map(p => p.propValue)) : prop_value,
    max: optimalPoints.length > 0 ? Math.max(...optimalPoints.map(p => p.propValue)) : prop_value,
  };
  
  // Calculate stability
  const confidenceVariance = calculateVariance(points.map(p => p.confidence));
  const stability = confidenceVariance < 50 ? 'Stable' : confidenceVariance < 150 ? 'Moderate' : 'Volatile';
  
  // Get confidence range
  const confidences = points.map(p => p.confidence);
  const maxConfidence = Math.max(...confidences);
  const minConfidence = Math.min(...confidences);
  
  return {
    points,
    turningPoint,
    optimalRange,
    stability,
    maxConfidence,
    minConfidence,
  };
}

function getRiskLevel(distance: number, expectedStat: number, volatility: number): 'Low' | 'Medium' | 'High' {
  const normalizedDistance = distance / (expectedStat * volatility);
  if (normalizedDistance < 1) return 'Low';
  if (normalizedDistance < 2) return 'Medium';
  return 'High';
}

function findTurningPoint(points: SensitivityPoint[]): SensitivityPoint | null {
  for (let i = 1; i < points.length; i++) {
    if (points[i].prediction !== points[i-1].prediction) {
      return points[i];
    }
  }
  return null;
}

function calculateVariance(values: number[]): number {
  const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
  const squaredDiffs = values.map(val => Math.pow(val - mean, 2));
  return squaredDiffs.reduce((sum, val) => sum + val, 0) / values.length;
}

function generateCurvePath(points: SensitivityPoint[]): string {
  if (points.length === 0) return '';
  
  const pathCommands = points.map((point, index) => {
    const x = 50 + ((point.propValue - points[0].propValue) / 
      (points[points.length - 1].propValue - points[0].propValue)) * 400;
    const y = 225 - (point.confidence * 1.75);
    return index === 0 ? `M ${x} ${y}` : `L ${x} ${y}`;
  });
  
  return pathCommands.join(' ');
}

function getCurrentPropX(propValue: number, points: SensitivityPoint[]): number {
  if (points.length === 0) return 250;
  
  const minVal = points[0].propValue;
  const maxVal = points[points.length - 1].propValue;
  const normalizedPos = (propValue - minVal) / (maxVal - minVal);
  return 50 + (normalizedPos * 400);
}

export default SensitivityCurve;