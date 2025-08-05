import React, { useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  useTheme,
  useMediaQuery,
  Paper,
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
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'));

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
    <Box sx={{ position: 'relative' }}>
      {/* Compact Header */}
      <Box sx={{ mb: 1.5, textAlign: 'center' }}>
        <Typography
          variant="h6"
          sx={{
            fontWeight: 600,
            color: 'text.primary',
            mb: 0.25,
          }}
        >
          Create Prediction
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Configure your prediction across all steps
        </Typography>
      </Box>

      {/* Horizontal Side-by-Side Layout */}
      <Box sx={{ 
        display: isMobile ? 'flex' : 'grid',
        flexDirection: isMobile ? 'column' : undefined,
        gridTemplateColumns: isMobile ? undefined : '1fr 1fr 1fr',
        gap: { xs: 1.5, lg: 2 },
        mb: 1.5,
      }}>
        {/* Player Selection Column */}
        <Paper 
          elevation={2}
          sx={{
            p: { xs: 1.5, sm: 2, md: 2, lg: 2.5, xl: 3 },
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
            minHeight: { xs: 'auto', md: 350, lg: 400, xl: 450 },
            position: 'relative',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              borderColor: 'rgba(63, 81, 181, 0.3)',
              boxShadow: '0 4px 20px rgba(63, 81, 181, 0.1)',
              transform: 'translateY(-2px)',
            },
          }}
        >
          <Box sx={{ 
            borderBottom: '2px solid rgba(63, 81, 181, 0.3)',
            pb: 1,
            mb: 2,
          }}>
            <Typography variant="subtitle1" sx={{ 
              fontWeight: 600,
              color: 'primary.main',
              textAlign: 'center'
            }}>
              ① Player & Position
            </Typography>
          </Box>
          <PlayerSelectionStep
            formData={formData}
            errors={errors}
            onChange={updateFormData}
          />
        </Paper>

        {/* Match Details Column */}
        <Paper 
          elevation={2}
          sx={{
            p: { xs: 1.5, sm: 2, md: 2, lg: 2.5, xl: 3 },
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
            minHeight: { xs: 'auto', md: 350, lg: 400, xl: 450 },
            position: 'relative',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              borderColor: 'rgba(245, 0, 87, 0.3)',
              boxShadow: '0 4px 20px rgba(245, 0, 87, 0.1)',
              transform: 'translateY(-2px)',
            },
          }}
        >
          <Box sx={{ 
            borderBottom: '2px solid rgba(245, 0, 87, 0.3)',
            pb: 1,
            mb: 2,
          }}>
            <Typography variant="subtitle1" sx={{ 
              fontWeight: 600,
              color: 'secondary.main',
              textAlign: 'center'
            }}>
              ② Match Details
            </Typography>
          </Box>
          <MatchDetailsStep
            formData={formData}
            errors={errors}
            onChange={updateFormData}
          />
        </Paper>

        {/* Prop Configuration Column */}
        <Paper 
          elevation={2}
          sx={{
            p: { xs: 1.5, sm: 2, md: 2, lg: 2.5, xl: 3 },
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
            minHeight: { xs: 'auto', md: 350, lg: 400, xl: 450 },
            position: 'relative',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              borderColor: 'rgba(76, 175, 80, 0.3)',
              boxShadow: '0 4px 20px rgba(76, 175, 80, 0.1)',
              transform: 'translateY(-2px)',
            },
          }}
        >
          <Box sx={{ 
            borderBottom: '2px solid rgba(76, 175, 80, 0.3)',
            pb: 1,
            mb: 2,
          }}>
            <Typography variant="subtitle1" sx={{ 
              fontWeight: 600,
              color: 'success.main',
              textAlign: 'center'
            }}>
              ③ Prop Configuration
            </Typography>
          </Box>
          <PropConfigurationStep
            formData={formData}
            errors={errors}
            onChange={updateFormData}
          />
        </Paper>
      </Box>

      {/* Centered Submit Button */}
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column',
        alignItems: 'center',
        mt: 1,
        gap: 1,
      }}>
        <Button
          onClick={handleSubmit}
          disabled={!isFormComplete() || loading}
          endIcon={loading ? 
            <AutoAwesome sx={{
              animation: 'spin 1s linear infinite',
              '@keyframes spin': {
                '0%': { transform: 'rotate(0deg)' },
                '100%': { transform: 'rotate(360deg)' },
              },
            }} /> : 
            <RocketLaunch />
          }
          variant="contained"
          size="large"
          sx={{
            px: 4,
            py: 1.5,
            fontSize: '1.1rem',
            fontWeight: 600,
            background: loading ? 
              'linear-gradient(45deg, #666, #999)' :
              'linear-gradient(45deg, #3f51b5, #f50057)',
            boxShadow: '0 4px 15px rgba(63, 81, 181, 0.4)',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              background: loading ? 
                'linear-gradient(45deg, #666, #999)' :
                'linear-gradient(45deg, #303f9f, #c51162)',
              boxShadow: '0 6px 20px rgba(63, 81, 181, 0.6)',
              transform: 'translateY(-2px)',
            },
            '&:disabled': {
              background: 'rgba(255, 255, 255, 0.1)',
              color: 'text.disabled',
              boxShadow: 'none',
            },
          }}
        >
          {loading ? 'Generating Prediction...' : 'Run'}
        </Button>

        {/* Status indicator */}       
        <Typography 
          variant="caption" 
          color={isFormComplete() ? 'success.main' : 'text.secondary'}
          sx={{ 
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 0.5,
            textAlign: 'center',
          }}
        >
          {isFormComplete() ? '✓ Ready to generate!' : 'Complete all sections above'}
        </Typography>
      </Box>
    </Box>
  );
};