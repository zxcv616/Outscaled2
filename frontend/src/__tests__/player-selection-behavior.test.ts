import { renderHook, act } from '@testing-library/react';
import { usePredictionForm } from '../components/enhanced/hooks/usePredictionForm';

describe('PlayerSelectionStep Behavior Test', () => {
  test('should simulate exactly what happens when Ice is added in PlayerSelectionStep', () => {
    const { result } = renderHook(() => usePredictionForm());

    console.log('=== INITIAL STATE ===');
    console.log('Players:', result.current.formData.player_names);
    console.log('Positions:', result.current.formData.position_roles);

    // Simulate what PlayerSelectionStep.handlePlayerChange does
    // When "Ice" is added with no suggestion
    const newPlayers = ['Ice'];
    const playerSuggestions = {}; // No suggestions for "Ice"
    const currentPositions = result.current.formData.position_roles || [];
    const newPositions: string[] = [];
    
    // Build new positions array like in PlayerSelectionStep
    for (let i = 0; i < newPlayers.length; i++) {
      const player = newPlayers[i];
      
      if (i < currentPositions.length && currentPositions[i]) {
        // Keep existing position if valid
        newPositions.push(currentPositions[i]);
      } else {
        // Try to get suggested position for new/empty slots
        const suggestedPosition = playerSuggestions[player] || '';
        newPositions.push(suggestedPosition);
      }
    }

    console.log('=== SIMULATED PlayerSelectionStep Logic ===');
    console.log('New players:', newPlayers);
    console.log('New positions:', newPositions);
    console.log('Current positions length:', currentPositions.length);

    // Apply the update
    act(() => {
      result.current.updateFormData({
        player_names: newPlayers,
        position_roles: newPositions,
      });
    });

    console.log('=== AFTER PLAYER SELECTION UPDATE ===');
    console.log('Players:', result.current.formData.player_names);
    console.log('Positions:', result.current.formData.position_roles);
    console.log('Position error:', result.current.getFieldError('position_roles'));
    console.log('Has position error:', result.current.hasFieldError('position_roles'));

    // Now check what happens if user tries to interact with positions
    // by simulating markPositionInteractionStarted
    act(() => {
      result.current.markPositionInteractionStarted();
    });

    console.log('=== AFTER POSITION INTERACTION STARTED ===');
    console.log('Position error:', result.current.getFieldError('position_roles'));
    console.log('Has position error:', result.current.hasFieldError('position_roles'));

    // After the fix, validation should not show errors until user actually interacts with positions
    // The onFocus trigger was removed, so validation should not be triggered automatically
    expect(result.current.hasFieldError('position_roles')).toBe(false);
    expect(result.current.getFieldError('position_roles')).toBe('');
  });

  test('should test validation behavior when step validation is triggered', () => {
    const { result } = renderHook(() => usePredictionForm());

    // Add Ice with empty position (what PlayerSelectionStep does)
    act(() => {
      result.current.updateFormData({
        player_names: ['Ice'],
        position_roles: [''], // Empty string position
      });
    });

    console.log('=== BEFORE STEP VALIDATION ===');
    console.log('Players:', result.current.formData.player_names);
    console.log('Positions:', result.current.formData.position_roles);
    console.log('Position error:', result.current.getFieldError('position_roles'));
    console.log('Has position error:', result.current.hasFieldError('position_roles'));

    // What happens when form tries to validate step (like clicking Next)
    let isStepValid = false;
    act(() => {
      isStepValid = result.current.validateStep(0);
    });

    console.log('=== AFTER STEP VALIDATION ===');
    console.log('Step valid:', isStepValid);
    console.log('Position error:', result.current.getFieldError('position_roles'));
    console.log('Has position error:', result.current.hasFieldError('position_roles'));

    // This should show the validation error
    expect(isStepValid).toBe(false);
    expect(result.current.hasFieldError('position_roles')).toBe(true);
    
    const errorMessage = result.current.getFieldError('position_roles');
    console.log('=== EXACT ERROR MESSAGE ===');
    console.log('"' + errorMessage + '"');
    
    // This should match what user reported
    expect(errorMessage).toBe('Please select a position for all players (1 position not assigned)');
  });
});