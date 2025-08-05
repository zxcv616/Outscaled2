import React, { useState } from 'react';
import { Container, Box, Typography, Paper } from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Header } from './components/Header';
import { EnhancedPredictionForm } from './components/enhanced/EnhancedPredictionForm';
import { EnhancedPredictionResult } from './components/enhanced/EnhancedPredictionResult';
import { predictionApi } from './services/api';
import { PredictionRequest, PredictionResponse } from './types/api';

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
  transitions: {
    duration: {
      shortest: 150,
      shorter: 200,
      short: 250,
      standard: 300,
      complex: 375,
      enteringScreen: 225,
      leavingScreen: 195,
    },
    easing: {
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
      fontSize: '2.5rem',
      '@media (max-width:600px)': {
        fontSize: '2rem',
      },
    },
    h2: {
      fontWeight: 600,
      fontSize: '2rem',
      '@media (max-width:600px)': {
        fontSize: '1.5rem',
      },
    },
    h3: {
      fontWeight: 600,
      fontSize: '1.75rem',
      '@media (max-width:600px)': {
        fontSize: '1.25rem',
      },
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.5rem',
      '@media (max-width:600px)': {
        fontSize: '1.125rem',
      },
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.25rem',
      '@media (max-width:600px)': {
        fontSize: '1rem',
      },
    },
    h6: {
      fontWeight: 500,
      fontSize: '1.1rem',
      '@media (max-width:600px)': {
        fontSize: '0.95rem',
      },
    },
    body1: {
      fontSize: '1rem',
      '@media (max-width:600px)': {
        fontSize: '0.9rem',
      },
    },
    body2: {
      fontSize: '0.875rem',
      '@media (max-width:600px)': {
        fontSize: '0.8rem',
      },
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
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            borderColor: 'rgba(255, 255, 255, 0.15)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: 8,
          padding: '12px 24px',
          minHeight: '48px',
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          transform: 'translateY(0px)',
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          '&:hover': {
            transform: 'translateY(-1px)',
            boxShadow: '0 4px 16px rgba(0,0,0,0.25)',
          },
          '&:active': {
            transform: 'translateY(0px)',
            transition: 'all 0.1s cubic-bezier(0.4, 0, 0.2, 1)',
          },
          '@media (max-width:600px)': {
            padding: '14px 20px',
            fontSize: '0.95rem',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: 'rgba(255, 255, 255, 0.3)',
              },
            },
            '&.Mui-focused': {
              transform: 'scale(1.02)',
              '& .MuiOutlinedInput-notchedOutline': {
                borderWidth: '2px',
                boxShadow: '0 0 0 1px rgba(63, 81, 181, 0.2)',
              },
            },
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          transform: 'translateY(0px)',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'scale(1.05)',
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
      console.error('Prediction error:', err);
      if (err instanceof Error) {
        setError(err.message);
      } else if (typeof err === 'string') {
        setError(err);
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
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
          
          <Container maxWidth="xl" sx={{ 
            py: 1,
            animation: 'fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
            '@keyframes fadeInUp': {
              '0%': {
                opacity: 0,
                transform: 'translateY(30px)',
              },
              '100%': {
                opacity: 1,
                transform: 'translateY(0px)',
              },
            },
          }}>
            <Box sx={{ 
              mb: 1.5, 
              textAlign: 'center',
              animation: 'fadeIn 0.8s cubic-bezier(0.4, 0, 0.2, 1) 0.2s both',
              '@keyframes fadeIn': {
                '0%': { opacity: 0 },
                '100%': { opacity: 1 },
              },
            }}>
              <Typography 
                variant="h2" 
                component="h1" 
                sx={{ 
                  fontWeight: 700,
                  background: 'linear-gradient(45deg, #3f51b5, #f50057)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  mb: 0.5,
                }}
              >
                League of Legends Prop Predictions
              </Typography>
              <Typography 
                variant="body1" 
                color="text.secondary" 
                sx={{ 
                  maxWidth: 600,
                  mx: 'auto',
                  lineHeight: 1.5,
                  opacity: 0.9,
                }}
              >
                AI-powered predictions for kills and assists prop bets using real match data
              </Typography>
            </Box>

            {/* Full Width Layout for Horizontal Form */}
            <Box sx={{ 
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              alignItems: 'center',
              width: '100%',
            }}>
              {/* Full Width Form */}
              <Paper 
                elevation={8} 
                sx={{ 
                  p: { xs: 2, sm: 3, md: 4 }, 
                  borderRadius: 2,
                  background: 'rgba(26, 26, 26, 0.95)',
                  backdropFilter: 'blur(20px)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  width: '100%',
                  maxWidth: { xs: '100%', sm: '100%', md: '100%', lg: '1400px', xl: '1600px' },
                }}
              >
                <EnhancedPredictionForm onSubmit={handlePrediction} loading={loading} />
              </Paper>
              
              {/* Results Section */}
              <Box sx={{ 
                width: '100%',
                maxWidth: { xs: '100%', sm: '100%', md: '100%', lg: '1400px', xl: '1600px' },
              }}>
                <EnhancedPredictionResult 
                  result={result} 
                  request={currentRequest}
                  loading={loading} 
                  error={error} 
                />
              </Box>
            </Box>

            {/* Disclaimer - Now integrated into results */}
          </Container>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;
