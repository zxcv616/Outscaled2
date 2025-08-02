import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  LinearProgress,
  Card,
  CardContent,
  Alert,
  Button,
  Snackbar,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Psychology,
  Analytics,
  ContentCopy,
  Warning,
} from '@mui/icons-material';
import { PredictionResponse, PredictionRequest } from '../types/api';
import PredictionCurve from './PredictionCurve';

interface PredictionResultProps {
  result: PredictionResponse | null;
  request: PredictionRequest | null;
  loading: boolean;
  error: string | null;
}

export const PredictionResult: React.FC<PredictionResultProps> = ({ result, request, loading, error }) => {
  const [showCopySuccess, setShowCopySuccess] = React.useState(false);

  const handleCopyToClipboard = async () => {
    if (!result) return;
    
    try {
      const completeData = {
        request: request,
        response: result,
        timestamp: new Date().toISOString()
      };
      const jsonData = JSON.stringify(completeData, null, 2);
      await navigator.clipboard.writeText(jsonData);
      setShowCopySuccess(true);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  if (loading) {
    return (
      <Paper 
        elevation={8} 
        sx={{ 
          p: 4, 
          mb: 4,
          borderRadius: 3,
          background: 'rgba(26, 26, 26, 0.95)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Analytics sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
          <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
            Analyzing Data...
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Our AI is processing your request and generating predictions
          </Typography>
        </Box>
        <LinearProgress 
          sx={{ 
            height: 8, 
            borderRadius: 4,
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            '& .MuiLinearProgress-bar': {
              background: 'linear-gradient(45deg, #3f51b5, #f50057)',
            },
          }} 
        />
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper 
        elevation={8} 
        sx={{ 
          p: 4, 
          mb: 4,
          borderRadius: 3,
          background: 'rgba(26, 26, 26, 0.95)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 0, 0, 0.3)',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Warning sx={{ fontSize: 32, color: 'error.main', mr: 2 }} />
          <Typography variant="h5" sx={{ fontWeight: 600, color: 'error.main' }}>
            Error
          </Typography>
        </Box>
        <Alert severity="error" sx={{ background: 'rgba(244, 67, 54, 0.1)', border: '1px solid rgba(244, 67, 54, 0.3)' }}>
          {error}
        </Alert>
      </Paper>
    );
  }

  if (!result) {
    return null;
  }

  const isOver = result.prediction === 'OVER';
  const confidenceColor = result.confidence >= 80 ? 'success' : 
                         result.confidence >= 60 ? 'warning' : 'error';



  return (
    <>
      <Paper 
        elevation={24} 
        sx={{ 
          p: 4, 
          mb: 4,
          borderRadius: 3,
          background: 'rgba(26, 26, 26, 0.95)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 48,
                height: 48,
                borderRadius: 2,
                background: isOver ? 'linear-gradient(45deg, #4caf50, #66bb6a)' : 'linear-gradient(45deg, #f44336, #ef5350)',
                mr: 2,
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
              }}
            >
              {isOver ? <TrendingUp sx={{ color: 'white' }} /> : <TrendingDown sx={{ color: 'white' }} />}
            </Box>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                {result.prediction}
              </Typography>
              <Typography variant="body1" color="text.secondary">
                AI Prediction
              </Typography>
            </Box>
          </Box>
          <Button
            variant="outlined"
            startIcon={<ContentCopy />}
            onClick={handleCopyToClipboard}
            sx={{ 
              borderColor: 'rgba(255, 255, 255, 0.3)',
              color: 'text.primary',
              '&:hover': {
                borderColor: 'primary.main',
                backgroundColor: 'rgba(63, 81, 181, 0.1)',
              },
            }}
          >
            Copy JSON
          </Button>
        </Box>

        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3, mb: 4 }}>
          {/* Confidence */}
          <Box sx={{ flex: { xs: 1, md: 4 } }}>
            <Card sx={{ 
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 2,
            }}>
              <CardContent sx={{ textAlign: 'center', p: 3 }}>
                <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
                  {result.confidence}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
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
          </Box>

          {/* Expected Stat */}
          <Box sx={{ flex: { xs: 1, md: 4 } }}>
            <Card sx={{ 
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 2,
            }}>
              <CardContent sx={{ textAlign: 'center', p: 3 }}>
                <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
                  {result.expected_stat.toFixed(1)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Expected {result.prop_type}
                </Typography>
              </CardContent>
            </Card>
          </Box>

          {/* Prop Value */}
          <Box sx={{ flex: { xs: 1, md: 4 } }}>
            <Card sx={{ 
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 2,
            }}>
              <CardContent sx={{ textAlign: 'center', p: 3 }}>
                <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
                  {result.prop_value}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Prop Line
                </Typography>
              </CardContent>
            </Card>
          </Box>
        </Box>

        {/* Reasoning */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Psychology sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              AI Reasoning
            </Typography>
          </Box>
          <Paper 
            sx={{ 
              p: 3,
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

        {/* Sample Details */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Analytics sx={{ mr: 1, color: 'secondary.main' }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Data Analysis
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
            <Box sx={{ flex: { xs: 1, md: 6 } }}>
              <Paper 
                sx={{ 
                  p: 2,
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: 2,
                }}
              >
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Data Years
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>
                  {result.data_years}
                </Typography>
              </Paper>
            </Box>
            <Box sx={{ flex: { xs: 1, md: 6 } }}>
              <Paper 
                sx={{ 
                  p: 2,
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: 2,
                }}
              >
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Maps Used
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>
                  {result.sample_details?.maps_used || 0} maps
                </Typography>
              </Paper>
            </Box>
          </Box>
        </Box>

        {/* Prediction Curve */}
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <TrendingUp sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Prediction Distribution
            </Typography>
          </Box>
          <Paper 
            sx={{ 
              p: 3,
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 2,
            }}
          >
            <PredictionCurve 
              expectedStat={result.expected_stat}
              propValue={result.prop_value}
              confidenceInterval={result.confidence_interval}
              prediction={result.prediction}
              confidence={result.confidence}
            />
          </Paper>
        </Box>
      </Paper>

      <Snackbar
        open={showCopySuccess}
        autoHideDuration={3000}
        onClose={() => setShowCopySuccess(false)}
        message="JSON data copied to clipboard!"
      />
    </>
  );
}; 