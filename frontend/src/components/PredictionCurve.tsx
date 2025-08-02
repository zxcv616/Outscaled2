import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
} from '@mui/material';

import { TrendingUp, TrendingDown } from '@mui/icons-material';

interface PredictionCurveProps {
  expectedStat: number;
  propValue: number;
  confidenceInterval: [number, number];
  prediction: 'OVER' | 'UNDER';
  confidence: number;
}

const PredictionCurve: React.FC<PredictionCurveProps> = ({ 
  expectedStat, 
  propValue, 
  confidenceInterval, 
  prediction,
  confidence
}) => {
  const isOver = prediction === 'OVER';
  const gap = Math.abs(expectedStat - propValue);
  const gapPercentage = (gap / propValue) * 100;

  // Calculate prediction strength based on confidence
  const getPredictionStrength = (confidence: number) => {
    if (confidence >= 85) return { label: 'Strong', color: 'success' as const };
    if (confidence >= 65) return { label: 'Moderate', color: 'warning' as const };
    return { label: 'Weak', color: 'error' as const };
  };

  const strength = getPredictionStrength(confidence);

  return (
    <Box>
      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
        {/* Visual Representation */}
        <Box sx={{ flex: { xs: 1, md: 8 } }}>
          <Box sx={{ position: 'relative', height: 120, mb: 2 }}>
            {/* Background scale */}
            <Box sx={{ 
              position: 'absolute', 
              top: 0, 
              left: 0, 
              right: 0, 
              height: '100%',
              background: 'linear-gradient(90deg, rgba(244, 67, 54, 0.1) 0%, rgba(255, 193, 7, 0.1) 50%, rgba(76, 175, 80, 0.1) 100%)',
              borderRadius: 2,
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }} />
            
            {/* Prop line marker */}
            <Box sx={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: '50%',
              width: 2,
              background: 'linear-gradient(180deg, #f50057, #ff4081)',
              transform: 'translateX(-50%)',
              borderRadius: 1,
              boxShadow: '0 2px 8px rgba(245, 0, 87, 0.4)',
            }} />
            
            {/* Expected stat marker */}
            <Box sx={{
              position: 'absolute',
              top: '50%',
              left: `${50 + (expectedStat - propValue) * 20}%`,
              transform: 'translate(-50%, -50%)',
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: isOver ? 'linear-gradient(45deg, #4caf50, #66bb6a)' : 'linear-gradient(45deg, #f44336, #ef5350)',
              border: '3px solid white',
              boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
              zIndex: 2,
            }} />
            
            {/* Confidence interval */}
            <Box sx={{
              position: 'absolute',
              top: '50%',
              left: `${50 + (confidenceInterval[0] - propValue) * 20}%`,
              right: `${50 - (confidenceInterval[1] - propValue) * 20}%`,
              height: 8,
              background: 'rgba(63, 81, 181, 0.3)',
              borderRadius: 4,
              transform: 'translateY(-50%)',
              border: '1px solid rgba(63, 81, 181, 0.5)',
            }} />
            
            {/* Labels */}
            <Box sx={{
              position: 'absolute',
              bottom: -30,
              left: '50%',
              transform: 'translateX(-50%)',
              textAlign: 'center',
            }}>
              <Typography variant="caption" color="text.secondary">
                Prop Line: {propValue}
              </Typography>
            </Box>
            
            <Box sx={{
              position: 'absolute',
              bottom: -30,
              left: `${50 + (expectedStat - propValue) * 20}%`,
              transform: 'translateX(-50%)',
              textAlign: 'center',
            }}>
              <Typography variant="caption" color="text.secondary">
                Expected: {expectedStat.toFixed(1)}
              </Typography>
            </Box>
          </Box>
          
          {/* Scale indicators */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', px: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Lower
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Higher
            </Typography>
          </Box>
        </Box>

        {/* Stats */}
        <Box sx={{ flex: { xs: 1, md: 4 } }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Paper sx={{ 
              p: 2,
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 2,
            }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Gap
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {gap.toFixed(1)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                ({gapPercentage.toFixed(1)}% of prop line)
              </Typography>
            </Paper>

            <Paper sx={{ 
              p: 2,
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 2,
            }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Confidence Interval
              </Typography>
              <Typography variant="body1" sx={{ fontWeight: 500 }}>
                [{confidenceInterval[0].toFixed(1)}, {confidenceInterval[1].toFixed(1)}]
              </Typography>
            </Paper>

            <Paper sx={{ 
              p: 2,
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 2,
            }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Prediction Strength
              </Typography>
              <Chip
                icon={isOver ? <TrendingUp /> : <TrendingDown />}
                label={strength.label}
                color={strength.color}
                size="small"
                sx={{ fontWeight: 600 }}
              />
            </Paper>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default PredictionCurve; 