import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Stepper,
  Step,
  StepLabel,
  Fade,
  Slide,
  useTheme,
  useMediaQuery,
  Fab,
  Zoom,
} from '@mui/material';
import {
  NavigateNext,
  NavigateBefore,
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

const steps = [
  { label: 'Players & Positions', icon: '👥' },
  { label: 'Match Details', icon: '🏆' },
  { label: 'Prop Configuration', icon: '📊' },
];

export const EnhancedPredictionForm: React.FC<EnhancedPredictionFormProps> = ({ 
  onSubmit, 
  loading 
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [activeStep, setActiveStep] = useState(0);
  const [slideDirection, setSlideDirection] = useState<'left' | 'right'>('left');

  const {
    formData,
    errors,
    isStepValid,
    isFormComplete,
    updateFormData,
    validateStep,
    submitForm,
    markPositionInteractionStarted,
  } = usePredictionForm();

  const handleNext = useCallback(() => {
    if (validateStep(activeStep)) {
      setSlideDirection('left');
      setActiveStep((prev) => Math.min(prev + 1, steps.length - 1));
    }
  }, [activeStep, validateStep]);

  const handleBack = useCallback(() => {
    setSlideDirection('right');
    setActiveStep((prev) => Math.max(prev - 1, 0));
  }, []);

  const handleStepClick = useCallback((step: number) => {
    if (step < activeStep || isStepValid(step)) {
      setSlideDirection(step > activeStep ? 'left' : 'right');
      setActiveStep(step);
    }
  }, [activeStep, isStepValid]);

  const handleSubmit = useCallback(() => {
    if (isFormComplete()) {
      submitForm(onSubmit);
    }
  }, [isFormComplete, submitForm, onSubmit]);

  const renderStepContent = (step: number) => {
    const slideProps = {
      direction: slideDirection,
      in: true,
      mountOnEnter: true,
      unmountOnExit: true,
      timeout: { enter: 300, exit: 200 },
    };

    switch (step) {
      case 0:
        return (
          <Slide {...slideProps}>
            <Box>
              <PlayerSelectionStep
                formData={formData}
                errors={errors}
                onChange={updateFormData}
                onPositionInteractionStart={markPositionInteractionStarted}
              />
            </Box>
          </Slide>
        );
      case 1:
        return (
          <Slide {...slideProps}>
            <Box>
              <MatchDetailsStep
                formData={formData}
                errors={errors}
                onChange={updateFormData}
              />
            </Box>
          </Slide>
        );
      case 2:
        return (
          <Slide {...slideProps}>
            <Box>
              <PropConfigurationStep
                formData={formData}
                errors={errors}
                onChange={updateFormData}
              />
            </Box>
          </Slide>
        );
      default:
        return null;
    }
  };

  const progressPercentage = ((activeStep + 1) / steps.length) * 100;

  return (
    <Box sx={{ position: 'relative' }}>
      {/* Progress Header */}
      <Paper
        elevation={2}
        sx={{
          p: 3,
          mb: 3,
          background: 'rgba(255, 255, 255, 0.03)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 3,
        }}
      >
        <Box sx={{ mb: 3, textAlign: 'center' }}>
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
            Step {activeStep + 1} of {steps.length}: {steps[activeStep].label}
          </Typography>
        </Box>

        {/* Progress Bar */}
        <Box
          sx={{
            height: 6,
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            borderRadius: 3,
            overflow: 'hidden',
            mb: 2,
          }}
        >
          <Box
            sx={{
              height: '100%',
              background: 'linear-gradient(45deg, #3f51b5, #f50057)',
              borderRadius: 3,
              width: `${progressPercentage}%`,
              transition: 'width 0.3s ease-in-out',
            }}
          />
        </Box>

        {/* Step Indicator */}
        <Stepper
          activeStep={activeStep}
          alternativeLabel={!isMobile}
          orientation={isMobile ? 'vertical' : 'horizontal'}
          sx={{
            '& .MuiStepLabel-label': {
              fontSize: isMobile ? '0.875rem' : '1rem',
              fontWeight: 500,
            },
            '& .MuiStepIcon-root': {
              fontSize: isMobile ? '1.5rem' : '2rem',
              '&.Mui-active': {
                color: theme.palette.primary.main,
              },
              '&.Mui-completed': {
                color: theme.palette.success.main,
              },
            },
          }}
        >
          {steps.map((step, index) => (
            <Step
              key={step.label}
              onClick={() => handleStepClick(index)}
              sx={{
                cursor: index <= activeStep || isStepValid(index) ? 'pointer' : 'default',
                '&:hover': {
                  '& .MuiStepLabel-label': {
                    color: theme.palette.primary.main,
                  },
                },
              }}
            >
              <StepLabel>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography component="span" sx={{ fontSize: '1.2rem' }}>
                    {step.icon}
                  </Typography>
                  {step.label}
                </Box>
              </StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      {/* Step Content */}
      <Paper
        elevation={8}
        sx={{
          p: 4,
          mb: 3,
          background: 'rgba(26, 26, 26, 0.95)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 3,
          minHeight: 400,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <Fade in={true} timeout={300}>
          <Box>{renderStepContent(activeStep)}</Box>
        </Fade>
      </Paper>

      {/* Navigation Controls */}
      <Paper
        elevation={4}
        sx={{
          p: 3,
          background: 'rgba(255, 255, 255, 0.03)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 3,
        }}
      >
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <Button
            onClick={handleBack}
            disabled={activeStep === 0}
            startIcon={<NavigateBefore />}
            variant="outlined"
            sx={{
              borderColor: 'rgba(255, 255, 255, 0.3)',
              color: 'text.primary',
              '&:hover': {
                borderColor: 'primary.main',
                backgroundColor: 'rgba(63, 81, 181, 0.1)',
              },
              '&:disabled': {
                borderColor: 'rgba(255, 255, 255, 0.1)',
                color: 'text.disabled',
              },
            }}
          >
            Back
          </Button>

          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ textAlign: 'center', flex: 1 }}
          >
            {activeStep === steps.length - 1
              ? 'Review your selections and generate prediction'
              : 'Complete this step to continue'}
          </Typography>

          {activeStep === steps.length - 1 ? (
            <Button
              onClick={handleSubmit}
              disabled={!isFormComplete() || loading}
              endIcon={loading ? <AutoAwesome /> : <RocketLaunch />}
              variant="contained"
              size="large"
              sx={{
                px: 4,
                py: 1.5,
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
              {loading ? 'Generating...' : 'Get AI Prediction'}
            </Button>
          ) : (
            <Button
              onClick={handleNext}
              disabled={!isStepValid(activeStep)}
              endIcon={<NavigateNext />}
              variant="contained"
              sx={{
                px: 3,
                py: 1.5,
                fontSize: '1rem',
                fontWeight: 600,
                background: 'linear-gradient(45deg, #3f51b5, #f50057)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #303f9f, #c51162)',
                },
                '&:disabled': {
                  background: 'rgba(255, 255, 255, 0.1)',
                  color: 'text.disabled',
                },
              }}
            >
              Next
            </Button>
          )}
        </Box>
      </Paper>

      {/* Mobile FAB for Quick Access */}
      {isMobile && (
        <Zoom in={activeStep === steps.length - 1 && isFormComplete()}>
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
    </Box>
  );
};