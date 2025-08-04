import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  Grid2,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  Warning,
  Timeline,
  TrendingUp,
  Security,
  CheckCircle,
} from '@mui/icons-material';
import { PredictionResponse } from '../../types/api';

interface VolatilityRiskClassificationProps {
  result: PredictionResponse;
}

interface RiskAssessment {
  volatilityScore: number;
  riskGrade: 'Low' | 'Moderate' | 'High' | 'Extreme';
  riskColor: 'success' | 'warning' | 'error';
  recommendation: string;
  riskFactors: string[];
  managementStrategy: string;
}

const VolatilityRiskClassification: React.FC<VolatilityRiskClassificationProps> = ({ result }) => {
  const assessment = calculateRiskAssessment(result);

  return (
    <Box>
      <Grid2 container spacing={3}>
        {/* Risk Overview */}
        <Grid2 size={{ xs: 12, md: 6 }}>
          <Paper sx={{ 
            p: 3, 
            background: 'rgba(255, 255, 255, 0.02)', 
            border: '1px solid rgba(255, 255, 255, 0.05)' 
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Security sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Risk Classification
              </Typography>
            </Box>
            
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <Typography variant="h2" sx={{ 
                fontWeight: 700, 
                color: assessment.riskColor === 'success' ? 'success.main' : 
                       assessment.riskColor === 'warning' ? 'warning.main' : 'error.main'
              }}>
                {assessment.riskGrade}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Risk Grade
              </Typography>
            </Box>

            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Volatility Score
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {assessment.volatilityScore}/100
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={assessment.volatilityScore}
                sx={{
                  height: 10,
                  borderRadius: 5,
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: assessment.riskColor === 'success' ? '#4caf50' : 
                                   assessment.riskColor === 'warning' ? '#ff9800' : '#f44336',
                  },
                }}
              />
            </Box>

            <Alert 
              severity={assessment.riskColor} 
              sx={{ 
                background: `rgba(${assessment.riskColor === 'success' ? '76, 175, 80' : 
                            assessment.riskColor === 'warning' ? '255, 152, 0' : '244, 67, 54'}, 0.1)`,
                border: `1px solid rgba(${assessment.riskColor === 'success' ? '76, 175, 80' : 
                        assessment.riskColor === 'warning' ? '255, 152, 0' : '244, 67, 54'}, 0.3)`
              }}
            >
              {assessment.recommendation}
            </Alert>
          </Paper>
        </Grid2>

        {/* Risk Factors */}
        <Grid2 size={{ xs: 12, md: 6 }}>
          <Paper sx={{ 
            p: 3, 
            background: 'rgba(255, 255, 255, 0.02)', 
            border: '1px solid rgba(255, 255, 255, 0.05)' 
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Warning sx={{ mr: 1, color: 'warning.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Risk Factors
              </Typography>
            </Box>

            <Box sx={{ mb: 3 }}>
              {assessment.riskFactors.map((factor, index) => (
                <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Box sx={{ 
                    width: 6, 
                    height: 6, 
                    borderRadius: '50%', 
                    backgroundColor: 'warning.main', 
                    mr: 1 
                  }} />
                  <Typography variant="body2">{factor}</Typography>
                </Box>
              ))}
            </Box>

            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                Management Strategy
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {assessment.managementStrategy}
              </Typography>
            </Box>
          </Paper>
        </Grid2>

        {/* Detailed Metrics */}
        <Grid2 size={{ xs: 12 }}>
          <Paper sx={{ 
            p: 3, 
            background: 'rgba(255, 255, 255, 0.02)', 
            border: '1px solid rgba(255, 255, 255, 0.05)' 
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Timeline sx={{ mr: 1, color: 'info.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Volatility Breakdown
              </Typography>
            </Box>

            <Grid2 container spacing={2}>
              <Grid2 size={{ xs: 12, sm: 3 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
                    {((result.sample_details?.volatility || 0.3) * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Historical Volatility
                  </Typography>
                </Box>
              </Grid2>
              
              <Grid2 size={{ xs: 12, sm: 3 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'secondary.main' }}>
                    {result.sample_details?.maps_used || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Sample Size
                  </Typography>
                </Box>
              </Grid2>
              
              <Grid2 size={{ xs: 12, sm: 3 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'info.main' }}>
                    {Math.abs(result.expected_stat - result.prop_value).toFixed(1)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Expected Gap
                  </Typography>
                </Box>
              </Grid2>
              
              <Grid2 size={{ xs: 12, sm: 3 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'success.main' }}>
                    {result.confidence}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Model Confidence
                  </Typography>
                </Box>
              </Grid2>
            </Grid2>
          </Paper>
        </Grid2>
      </Grid2>
    </Box>
  );
};

function calculateRiskAssessment(result: PredictionResponse): RiskAssessment {
  const volatility = result.sample_details?.volatility || 0.3;
  const sampleSize = result.sample_details?.maps_used || 0;
  const confidence = result.confidence;
  const gap = Math.abs(result.expected_stat - result.prop_value);
  
  // Calculate volatility score (0-100)
  const volatilityScore = Math.min(100, volatility * 200); // Scale 0.5 volatility to 100 score
  
  // Determine risk grade
  let riskGrade: 'Low' | 'Moderate' | 'High' | 'Extreme';
  let riskColor: 'success' | 'warning' | 'error';
  
  if (volatilityScore < 30) {
    riskGrade = 'Low';
    riskColor = 'success';
  } else if (volatilityScore < 50) {
    riskGrade = 'Moderate';
    riskColor = 'warning';
  } else if (volatilityScore < 70) {
    riskGrade = 'High';
    riskColor = 'error';
  } else {
    riskGrade = 'Extreme';
    riskColor = 'error';
  }
  
  // Generate risk factors
  const riskFactors: string[] = [];
  if (volatility > 0.4) riskFactors.push('High historical volatility detected');
  if (sampleSize < 10) riskFactors.push('Limited sample size increases uncertainty');
  if (confidence < 70) riskFactors.push('Low model confidence indicates uncertainty');
  if (gap > result.expected_stat * 0.3) riskFactors.push('Large gap between prop and expected value');
  if (result.sample_details?.fallback_used) riskFactors.push('Fallback data used due to insufficient direct data');
  
  if (riskFactors.length === 0) {
    riskFactors.push('No significant risk factors identified');
  }
  
  // Generate recommendation
  let recommendation: string;
  if (riskGrade === 'Low') {
    recommendation = 'Low risk profile. This prediction appears stable with good historical data support.';
  } else if (riskGrade === 'Moderate') {
    recommendation = 'Moderate risk. Consider position sizing and monitor for data quality issues.';
  } else if (riskGrade === 'High') {
    recommendation = 'High risk detected. Use caution and consider reducing exposure or waiting for better opportunities.';
  } else {
    recommendation = 'Extreme risk warning. This prediction has very high volatility. Avoid or use minimal position size.';
  }
  
  // Generate management strategy
  let managementStrategy: string;
  if (riskGrade === 'Low') {
    managementStrategy = 'Standard position sizing appropriate. Monitor for any changes in player form or team dynamics.';
  } else if (riskGrade === 'Moderate') {
    managementStrategy = 'Reduce position size by 25-50%. Set stricter loss limits and consider hedging strategies.';
  } else if (riskGrade === 'High') {
    managementStrategy = 'Minimal position size recommended. Extensive research required before commitment. Consider waiting for better data.';
  } else {
    managementStrategy = 'Avoid this prediction entirely or use only for entertainment with minimal risk capital.';
  }
  
  return {
    volatilityScore,
    riskGrade,
    riskColor,
    recommendation,
    riskFactors,
    managementStrategy,
  };
}

export default VolatilityRiskClassification;