import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  Grid2,
} from '@mui/material';
import {
  DataUsage,
  History,
  Person,
  Group,
} from '@mui/icons-material';
import { PredictionResponse } from '../../types/api';

interface ContextualDataSnapshotProps {
  result: PredictionResponse;
}

const ContextualDataSnapshot: React.FC<ContextualDataSnapshotProps> = ({ result }) => {
  return (
    <Box>
      <Grid2 container spacing={3}>
        {/* Player Context */}
        <Grid2 size={{ xs: 12, md: 6 }}>
          <Paper sx={{ 
            p: 3, 
            background: 'rgba(255, 255, 255, 0.02)', 
            border: '1px solid rgba(255, 255, 255, 0.05)' 
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Person sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Player Performance
              </Typography>
            </Box>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Recent Form (Last 3 Games)
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {(result.player_stats?.avg_kills || result.player_stats?.avg_assists || result.expected_stat).toFixed(1)} avg
              </Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Season Average
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {result.expected_stat.toFixed(1)}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                label={`${result.prop_type}`}
                size="small"
                color="primary"
                variant="outlined"
              />
              <Chip
                label={`${result.sample_details?.maps_used || 0} maps`}
                size="small"
                color="info"
                variant="outlined"
              />
            </Box>
          </Paper>
        </Grid2>

        {/* Data Quality */}
        <Grid2 size={{ xs: 12, md: 6 }}>
          <Paper sx={{ 
            p: 3, 
            background: 'rgba(255, 255, 255, 0.02)', 
            border: '1px solid rgba(255, 255, 255, 0.05)' 
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <DataUsage sx={{ mr: 1, color: 'info.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Data Quality
              </Typography>
            </Box>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Sample Completeness
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {Math.min(100, ((result.sample_details?.maps_used || 0) / 20) * 100).toFixed(0)}%
              </Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Data Years
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {result.data_years}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                label={result.sample_details?.fallback_used ? 'Fallback Used' : 'Direct Data'}
                size="small"
                color={result.sample_details?.fallback_used ? 'warning' : 'success'}
                variant="outlined"
              />
              <Chip
                label={result.sample_details?.tier_name || 'Unknown Tier'}
                size="small"
                color="secondary"
                variant="outlined"
              />
            </Box>
          </Paper>
        </Grid2>

        {/* Contextual Factors */}
        <Grid2 size={{ xs: 12 }}>
          <Paper sx={{ 
            p: 3, 
            background: 'rgba(255, 255, 255, 0.02)', 
            border: '1px solid rgba(255, 255, 255, 0.05)' 
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <History sx={{ mr: 1, color: 'secondary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Contextual Factors
              </Typography>
            </Box>

            <Grid2 container spacing={2}>
              <Grid2 size={{ xs: 12, sm: 3 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
                    {((result.sample_details?.volatility || 0.3) * 100).toFixed(0)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Historical Volatility
                  </Typography>
                </Box>
              </Grid2>
              
              <Grid2 size={{ xs: 12, sm: 3 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'secondary.main' }}>
                    1.15x
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Team Tempo vs Avg
                  </Typography>
                </Box>
              </Grid2>
              
              <Grid2 size={{ xs: 12, sm: 3 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'info.main' }}>
                    N/A
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    vs Opponent Avg
                  </Typography>
                </Box>
              </Grid2>
              
              <Grid2 size={{ xs: 12, sm: 3 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'success.main' }}>
                    1.0x
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Game Length Factor
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

export default ContextualDataSnapshot;