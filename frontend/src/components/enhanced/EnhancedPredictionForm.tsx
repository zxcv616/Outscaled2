import React, { useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  useTheme,
  useMediaQuery,
  Fab,
  Zoom,
  Container,
} from '@mui/material';
import {
  RocketLaunch,
  AutoAwesome,
} from '@mui/icons-material';
import { PredictionRequest } from '../../types/api';
import { PlayerSelectionStep } from './steps/PlayerSelectionStep';
import { MatchDetailsStep } from './steps/MatchDetailsStep';
import { PropConfigurationStep } from './steps/PropConfigurationStep';
import { usePredictionForm } from './hooks/usePredictionForm';

interface EnhancedPredictionFormProps {
  onSubmit: (request: PredictionRequest) => void;
  loading: boolean;
}

export const EnhancedPredictionForm: React.FC<EnhancedPredictionFormProps> = ({ 
  onSubmit, 
  loading 
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const {
    formData,
    errors,
    isFormComplete,
    updateFormData,
    submitForm,
  } = usePredictionForm();

  const handleSubmit = useCallback(() => {
    if (isFormComplete()) {
      submitForm(onSubmit);
    }
  }, [isFormComplete, submitForm, onSubmit]);

  return (
    <Container maxWidth="lg" sx={{ position: 'relative' }}>
      {/* Header */}
      <Paper
        elevation={2}
        sx={{
          p: 3,
          mb: 3,
          background: 'rgba(255, 255, 255, 0.03)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 3,
          textAlign: 'center',
        }}
      >
        <Typography
          variant="h4"
          gutterBottom
          sx={{
            fontWeight: 700,
            background: 'linear-gradient(45deg, #3f51b5, #f50057)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mb: 1,
          }}
        >
          Create Your Prediction
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Select a player, set your prop, and get AI-powered predictions
        </Typography>
      </Paper>

      {/* Form Content */}
      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
        {/* Player & Position Selection */}
        <Box sx={{ flex: 1 }}>
          <Paper
            elevation={8}
            sx={{
              p: 4,
              background: 'rgba(26, 26, 26, 0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 3,
              height: 'fit-content',
            }}
          >
            <PlayerSelectionStep
              formData={formData}
              errors={errors}
              onChange={updateFormData}
            />
          </Paper>
        </Box>

        {/* Match Details & Prop Configuration */}
        <Box sx={{ flex: 1 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Match Details */}
            <Paper
              elevation={8}
              sx={{
                p: 4,
                background: 'rgba(26, 26, 26, 0.95)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: 3,
              }}
            >
              <MatchDetailsStep
                formData={formData}
                errors={errors}
                onChange={updateFormData}
              />
            </Paper>

            {/* Prop Configuration */}
            <Paper
              elevation={8}
              sx={{
                p: 4,
                background: 'rgba(26, 26, 26, 0.95)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: 3,
              }}
            >
              <PropConfigurationStep
                formData={formData}
                errors={errors}
                onChange={updateFormData}
              />
            </Paper>
          </Box>
        </Box>
      </Box>

      {/* Submit Button */}
      <Paper
        elevation={4}
        sx={{
          p: 3,
          mt: 3,
          background: 'rgba(255, 255, 255, 0.03)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 3,
          textAlign: 'center',
        }}
      >
        <Button
          onClick={handleSubmit}
          disabled={!isFormComplete() || loading}
          endIcon={loading ? <AutoAwesome /> : <RocketLaunch />}
          variant="contained"
          size="large"
          sx={{
            px: 6,
            py: 2,
            fontSize: '1.1rem',
            fontWeight: 600,
            background: 'linear-gradient(45deg, #3f51b5, #f50057)',
            '&:hover': {
              background: 'linear-gradient(45deg, #303f9f, #c51162)',
            },
            boxShadow: '0 8px 32px rgba(63, 81, 181, 0.3)',
            '&:disabled': {
              background: 'rgba(255, 255, 255, 0.1)',
              color: 'text.disabled',
            },
          }}
        >
          {loading ? 'Generating Prediction...' : 'Get AI Prediction'}
        </Button>
        
        <Typography 
          variant="body2" 
          color="text.secondary" 
          sx={{ mt: 2 }}
        >
          {isFormComplete() 
            ? 'All fields complete - ready to generate prediction!' 
            : 'Please complete all required fields above'
          }
        </Typography>
      </Paper>

      {/* Mobile FAB for Quick Access */}
      {isMobile && (
        <Zoom in={isFormComplete()}>
          <Fab
            color="primary"
            onClick={handleSubmit}
            disabled={loading}
            sx={{
              position: 'fixed',
              bottom: 24,
              right: 24,
              zIndex: 1000,
              background: 'linear-gradient(45deg, #3f51b5, #f50057)',
              '&:hover': {
                background: 'linear-gradient(45deg, #303f9f, #c51162)',
              },
            }}
          >
            <RocketLaunch />
          </Fab>
        </Zoom>
      )}
    </Container>
  );
};