import React, { useEffect } from 'react';
import { Box, Typography, Button, Alert } from '@mui/material';
import { usePredictionForm } from './components/enhanced/hooks/usePredictionForm';

export const DebugValidation: React.FC = () => {
  const {
    formData,
    updateFormData,
    validateStep,
    getFieldError,
    hasFieldError,
  } = usePredictionForm();

  useEffect(() => {
    console.log('=== DEBUG VALIDATION COMPONENT LOADED ===');
    console.log('Current form data:', formData);
    console.log('Position error:', getFieldError('position_roles'));
    console.log('Has position error:', hasFieldError('position_roles'));
  }, [formData, getFieldError, hasFieldError]);

  const handleAddPlayer = () => {
    console.log('=== ADDING PLAYER Ice ===');
    updateFormData({
      player_names: ['Ice'],
    });
  };

  const handleMarkInteraction = () => {
    console.log('=== MARKING POSITION INTERACTION STARTED ===');
    // Function removed - interaction is now handled automatically
  };

  const handleValidateStep = () => {
    console.log('=== VALIDATING STEP 0 ===');
    const isValid = validateStep(0);
    console.log('Step 0 is valid:', isValid);
    console.log('Position error after validation:', getFieldError('position_roles'));
  };

  const handleAddPosition = () => {
    console.log('=== ADDING EMPTY POSITION ===');
    updateFormData({
      position_roles: [''],
    });
  };

  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" sx={{ mb: 4 }}>
        Validation Debug Panel
      </Typography>

      <Box sx={{ mb: 3 }}>
        <Typography variant="h6">Current State:</Typography>
        <Typography>Players: {JSON.stringify(formData.player_names)}</Typography>
        <Typography>Positions: {JSON.stringify(formData.position_roles)}</Typography>
        <Typography>Position Error: "{getFieldError('position_roles')}"</Typography>
        <Typography>Has Position Error: {hasFieldError('position_roles').toString()}</Typography>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <Button variant="contained" onClick={handleAddPlayer}>
          Add Player "Ice"
        </Button>
        <Button variant="contained" onClick={handleAddPosition}>
          Add Empty Position
        </Button>
        <Button variant="contained" onClick={handleMarkInteraction}>
          Mark Position Interaction Started
        </Button>
        <Button variant="contained" onClick={handleValidateStep}>
          Validate Step 0
        </Button>
      </Box>

      {hasFieldError('position_roles') && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <strong>Validation Error:</strong> {getFieldError('position_roles')}
        </Alert>
      )}

      <Box sx={{ mt: 4, p: 2, bgcolor: 'background.paper', borderRadius: 2 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Test Sequence:</Typography>
        <Typography variant="body2" sx={{ mb: 1 }}>
          1. Add player "Ice" - should NOT show validation error
        </Typography>
        <Typography variant="body2" sx={{ mb: 1 }}>
          2. Mark interaction started - should show validation error for empty position
        </Typography>
        <Typography variant="body2" sx={{ mb: 1 }}>
          3. Validate step - should show validation error
        </Typography>
      </Box>
    </Box>
  );
};