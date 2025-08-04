import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid2,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
} from '@mui/material';
import {
  ExpandMore,
  Code,
  DataObject,
  Timeline,
  Settings,
} from '@mui/icons-material';
import { PredictionResponse, PredictionRequest } from '../../types/api';

interface ExpandableMetadataProps {
  result: PredictionResponse;
  request: PredictionRequest | null;
}

const ExpandableMetadata: React.FC<ExpandableMetadataProps> = ({ result, request }) => {
  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Code sx={{ mr: 1, color: 'secondary.main' }} />
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Technical Metadata
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {/* Model Information */}
        <Accordion
          sx={{ 
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(255, 255, 255, 0.05)',
          }}
        >
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Settings sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                Model Configuration
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Grid2 container spacing={2}>
              <Grid2 size={{ xs: 12, md: 6 }}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">Model Version</Typography>
                  <Typography variant="body1">v2.1.3 (Primary Model)</Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">Training Date</Typography>
                  <Typography variant="body1">2024-07-15</Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">Confidence Method</Typography>
                  <Typography variant="body1">{result.sample_details?.ci_method || 'Bootstrap'}</Typography>
                </Box>
              </Grid2>
              <Grid2 size={{ xs: 12, md: 6 }}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">Feature Count</Typography>
                  <Typography variant="body1">127 features</Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">Model Type</Typography>
                  <Typography variant="body1">Ensemble (XGBoost + Neural)</Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">Cross-Validation</Typography>
                  <Typography variant="body1">5-fold temporal split</Typography>
                </Box>
              </Grid2>
            </Grid2>
          </AccordionDetails>
        </Accordion>

        {/* Feature Importance */}
        <Accordion
          sx={{ 
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(255, 255, 255, 0.05)',
          }}
        >
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Timeline sx={{ mr: 1, color: 'info.main' }} />
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                Feature Importance
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Top Contributing Features (SHAP values)
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Recent Performance (5 games)</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>0.62</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Position Factor</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>0.21</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Opponent Meta Score</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>0.14</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Map Pool Affinity</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>0.08</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Team Synergy Rating</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>0.06</Typography>
                </Box>
              </Box>
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* Request Data */}
        {request && (
          <Accordion
            sx={{ 
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid rgba(255, 255, 255, 0.05)',
            }}
          >
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <DataObject sx={{ mr: 1, color: 'secondary.main' }} />
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  Request Parameters
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Paper sx={{ 
                p: 2, 
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: 1,
              }}>
                <Typography variant="caption" color="text.secondary" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(request, null, 2)}
                </Typography>
              </Paper>
            </AccordionDetails>
          </Accordion>
        )}

        {/* Raw Response */}
        <Accordion
          sx={{ 
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(255, 255, 255, 0.05)',
          }}
        >
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <DataObject sx={{ mr: 1, color: 'warning.main' }} />
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                Raw Response Data
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Paper sx={{ 
              p: 2, 
              background: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 1,
              maxHeight: 400,
              overflow: 'auto',
            }}>
              <Typography variant="caption" color="text.secondary" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(result, null, 2)}
              </Typography>
            </Paper>
          </AccordionDetails>
        </Accordion>
      </Box>
    </Box>
  );
};

export default ExpandableMetadata;