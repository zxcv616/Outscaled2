import React from 'react';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  StepConnector,
  Typography,
  LinearProgress,
  Chip,
  useTheme,
  alpha,
  stepConnectorClasses,
  StepIconProps,
  styled,
} from '@mui/material';
import {
  Person,
  Sports,
  TrendingUp,
  CheckCircle,
  RadioButtonUnchecked,
  Warning,
} from '@mui/icons-material';
import { FormStep } from '../../hooks/usePredictionForm';

interface FormStepperProps {
  steps: FormStep[];
  currentStep: number;
  onStepClick: (stepIndex: number) => void;
  progressPercentage: number;
  allowStepNavigation?: boolean;
}

const CustomConnector = styled(StepConnector)(({ theme }) => ({
  [`&.${stepConnectorClasses.alternativeLabel}`]: {
    top: 22,
  },
  [`&.${stepConnectorClasses.active}`]: {
    [`& .${stepConnectorClasses.line}`]: {
      background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
    },
  },
  [`&.${stepConnectorClasses.completed}`]: {
    [`& .${stepConnectorClasses.line}`]: {
      background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
    },
  },
  [`& .${stepConnectorClasses.line}`]: {
    height: 3,
    border: 0,
    backgroundColor: alpha(theme.palette.text.secondary, 0.2),
    borderRadius: 1,
    transition: 'all 0.3s ease',
  },
}));

const StepIconRoot = styled('div')<{
  ownerState: { completed?: boolean; active?: boolean; error?: boolean };
}>(({ theme, ownerState }) => ({
  backgroundColor: ownerState.error
    ? theme.palette.error.main
    : ownerState.completed
    ? theme.palette.primary.main
    : ownerState.active
    ? theme.palette.primary.main
    : alpha(theme.palette.text.secondary, 0.3),
  zIndex: 1,
  color: '#fff',
  width: 44,
  height: 44,
  display: 'flex',
  borderRadius: '50%',
  justifyContent: 'center',
  alignItems: 'center',
  transition: 'all 0.3s ease',
  border: `3px solid ${
    ownerState.active || ownerState.completed
      ? theme.palette.primary.main
      : alpha(theme.palette.text.secondary, 0.2)
  }`,
  background: ownerState.active || ownerState.completed
    ? `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`
    : alpha(theme.palette.background.paper, 0.8),
  backdropFilter: 'blur(10px)',
  boxShadow: ownerState.active || ownerState.completed
    ? `0 4px 12px ${alpha(theme.palette.primary.main, 0.4)}`
    : 'none',
  cursor: 'pointer',
  '&:hover': {
    transform: 'scale(1.1)',
    boxShadow: `0 6px 16px ${alpha(theme.palette.primary.main, 0.3)}`,
  },
}));

const CustomStepIcon: React.FC<StepIconProps & { stepIndex: number; hasError: boolean }> = (props) => {
  const { active, completed, className, stepIndex, hasError } = props;

  const getIcon = (index: number) => {
    switch (index) {
      case 0:
        return <Person />;
      case 1:
        return <Sports />;
      case 2:
        return <TrendingUp />;
      default:
        return <RadioButtonUnchecked />;
    }
  };

  return (
    <StepIconRoot ownerState={{ completed, active, error: hasError }} className={className}>
      {hasError ? (
        <Warning />
      ) : completed ? (
        <CheckCircle />
      ) : (
        getIcon(stepIndex)
      )}
    </StepIconRoot>
  );
};

export const FormStepper: React.FC<FormStepperProps> = ({
  steps,
  currentStep,
  onStepClick,
  progressPercentage,
  allowStepNavigation = true,
}) => {
  const theme = useTheme();

  const handleStepClick = (stepIndex: number) => {
    if (allowStepNavigation && stepIndex <= currentStep) {
      onStepClick(stepIndex);
    }
  };

  return (
    <Box sx={{ width: '100%', mb: 4 }}>
      {/* Progress Bar */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Step {currentStep + 1} of {steps.length}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {Math.round(progressPercentage)}% Complete
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={progressPercentage}
          sx={{
            height: 8,
            borderRadius: 4,
            backgroundColor: alpha(theme.palette.text.secondary, 0.1),
            '& .MuiLinearProgress-bar': {
              background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
              borderRadius: 4,
              transition: 'transform 0.6s ease',
            },
          }}
        />
      </Box>

      {/* Step Labels and Current Step Info */}
      <Box sx={{ mb: 4 }}>
        <Stepper
          alternativeLabel
          activeStep={currentStep}
          connector={<CustomConnector />}
          sx={{
            '& .MuiStepLabel-root': {
              cursor: allowStepNavigation ? 'pointer' : 'default',
            },
          }}
        >
          {steps.map((step, index) => {
            const isCompleted = step.isValid && index < currentStep;
            const isActive = index === currentStep;
            const hasError = index === currentStep && !step.isValid && currentStep > 0;
            const isClickable = allowStepNavigation && index <= currentStep;

            return (
              <Step key={step.id} completed={isCompleted}>
                <StepLabel
                  StepIconComponent={(props) => (
                    <CustomStepIcon {...props} stepIndex={index} hasError={hasError} />
                  )}
                  onClick={() => isClickable && handleStepClick(index)}
                  sx={{
                    '& .MuiStepLabel-label': {
                      fontSize: '0.875rem',
                      fontWeight: isActive ? 600 : 400,
                      color: isActive
                        ? theme.palette.primary.main
                        : hasError
                        ? theme.palette.error.main
                        : 'text.secondary',
                      transition: 'all 0.3s ease',
                      mt: 1,
                    },
                  }}
                >
                  {step.title}
                </StepLabel>
              </Step>
            );
          })}
        </Stepper>
      </Box>

      {/* Current Step Details */}
      <Box
        sx={{
          textAlign: 'center',
          p: 3,
          background: alpha(theme.palette.background.paper, 0.5),
          backdropFilter: 'blur(10px)',
          borderRadius: 2,
          border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 2,
            background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
          },
        }}
      >
        <Typography
          variant="h5"
          sx={{
            fontWeight: 700,
            mb: 1,
            background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          {steps[currentStep]?.title}
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          {steps[currentStep]?.description}
        </Typography>
        
        {/* Step Status */}
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1 }}>
          {steps[currentStep]?.isValid ? (
            <Chip
              icon={<CheckCircle />}
              label="Complete"
              color="success"
              size="small"
              sx={{ fontWeight: 500 }}
            />
          ) : (
            <Chip
              icon={<Warning />}
              label="Incomplete"
              color="warning"
              size="small"
              sx={{ fontWeight: 500 }}
            />
          )}
        </Box>
      </Box>
    </Box>
  );
};