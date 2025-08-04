import React, { useState } from 'react';
import { Container, Box, Alert, Typography, Paper } from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Header } from './components/Header';
import { OptimizedPredictionForm } from './components/OptimizedPredictionForm';
import { PredictionResult } from './components/PredictionResult';
import { predictionApi } from './services/api';
import { PredictionRequest, PredictionResponse } from './types/api';
import { queryClient } from './lib/queryClient';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#3f51b5',
    },
    secondary: {
      main: '#f50057',
    },
    background: {
      default: '#0a0a0a',
      paper: 'rgba(26, 26, 26, 0.95)',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b0b0b0',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
      fontSize: '2.5rem',
    },
    h2: {
      fontWeight: 600,
      fontSize: '2rem',
    },
    h3: {
      fontWeight: 600,
      fontSize: '1.75rem',
    },
    h6: {
      fontWeight: 500,
      fontSize: '1.1rem',
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: 8,
          padding: '10px 24px',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        },
      },
    },
  },
});

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [currentRequest, setCurrentRequest] = useState<PredictionRequest | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handlePrediction = async (request: PredictionRequest) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setCurrentRequest(request);

    try {
      const prediction = await predictionApi.getPrediction(request);
      setResult(prediction);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box 
          sx={{ 
            minHeight: '100vh',
            backgroundImage: 'url(/background.jpg)',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundAttachment: 'fixed',
            position: 'relative',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.6)',
              zIndex: 1,
            },
          }}
        >
        <Box sx={{ position: 'relative', zIndex: 2 }}>
          <Header />
          
          <Container maxWidth="lg" sx={{ py: 4 }}>
            <Box sx={{ mb: 6, textAlign: 'center' }}>
              <Typography 
                variant="h1" 
                component="h1" 
                gutterBottom 
                sx={{ 
                  fontWeight: 800,
                  background: 'linear-gradient(45deg, #3f51b5, #f50057)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  mb: 2,
                  textShadow: '0 4px 8px rgba(0,0,0,0.3)',
                }}
              >
                League of Legends
              </Typography>
              <Typography 
                variant="h2" 
                component="h2" 
                gutterBottom 
                sx={{ 
                  fontWeight: 700,
                  color: 'text.primary',
                  mb: 2,
                }}
              >
                Prop Predictions
              </Typography>
              <Typography 
                variant="h6" 
                color="text.secondary" 
                sx={{ 
                  maxWidth: 600,
                  mx: 'auto',
                  lineHeight: 1.6,
                  opacity: 0.9,
                }}
              >
                AI-powered predictions for kills and assists prop bets using real match data from professional League of Legends tournaments
              </Typography>
            </Box>

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
              <OptimizedPredictionForm onSubmit={handlePrediction} loading={loading} />
            </Paper>
            
            <PredictionResult 
              result={result} 
              request={currentRequest}
              loading={loading} 
              error={error} 
            />

            {result && (
              <Paper 
                elevation={8} 
                sx={{ 
                  mt: 3, 
                  p: 3,
                  borderRadius: 2,
                  background: 'rgba(26, 26, 26, 0.9)',
                  backdropFilter: 'blur(15px)',
                }}
              >
                <Alert 
                  severity="info" 
                  sx={{ 
                    background: 'rgba(3, 169, 244, 0.1)',
                    border: '1px solid rgba(3, 169, 244, 0.3)',
                    borderRadius: 2,
                  }}
                >
                  <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                    <strong>Disclaimer:</strong> These predictions are for entertainment purposes only. 
                    Always gamble responsibly and never bet more than you can afford to lose.
                  </Typography>
                </Alert>
              </Paper>
            )}
          </Container>
        </Box>
      </Box>
      <ReactQueryDevtools initialIsOpen={false} />
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
