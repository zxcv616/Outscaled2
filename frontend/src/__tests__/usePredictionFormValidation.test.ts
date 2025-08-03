import { renderHook, act } from '@testing-library/react';
import { usePredictionForm } from '../components/enhanced/hooks/usePredictionForm';

describe('usePredictionForm - Position Validation Fix', () => {
  test('should not show position validation error immediately after player selection', () => {
    const { result } = renderHook(() => usePredictionForm());

    // Add a player
    act(() => {
      result.current.updateFormData({
        player_names: ['TestPlayer1'],
      });
    });

    // Check that no position error is shown initially
    expect(result.current.getFieldError('position_roles')).toBe('');
    expect(result.current.hasFieldError('position_roles')).toBe(false);
  });

  test('should show position validation error after user interacts with positions', () => {
    const { result } = renderHook(() => usePredictionForm());

    // Add a player
    act(() => {
      result.current.updateFormData({
        player_names: ['TestPlayer1'],
      });
    });

    // Simulate user interaction with positions
    act(() => {
      result.current.markPositionInteractionStarted();
    });

    // Update positions (simulating user interaction)
    act(() => {
      result.current.updateFormData({
        position_roles: [''], // Empty position should trigger error
      });
    });

    // Now position error should be shown
    expect(result.current.hasFieldError('position_roles')).toBe(true);
    expect(result.current.getFieldError('position_roles')).toContain('not assigned');
  });

  test('should show position validation error when trying to progress step', () => {
    const { result } = renderHook(() => usePredictionForm());

    // Add a player but no positions
    act(() => {
      result.current.updateFormData({
        player_names: ['TestPlayer1'],
        position_roles: [''], // Empty position
      });
    });

    // Trying to validate step should force position validation
    let isStepValid = false;
    act(() => {
      isStepValid = result.current.validateStep(0);
    });

    expect(isStepValid).toBe(false);
    expect(result.current.hasFieldError('position_roles')).toBe(true);
  });

  test('should allow progression when positions are properly assigned', () => {
    const { result } = renderHook(() => usePredictionForm());

    // Add a player with valid position
    act(() => {
      result.current.updateFormData({
        player_names: ['TestPlayer1'],
        position_roles: ['TOP'],
      });
    });

    // Step should be valid
    let isStepValid = false;
    act(() => {
      isStepValid = result.current.validateStep(0);
    });

    expect(isStepValid).toBe(true);
    expect(result.current.hasFieldError('position_roles')).toBe(false);
  });

  test('should not show validation errors when no players are selected', () => {
    const { result } = renderHook(() => usePredictionForm());

    // No players selected
    act(() => {
      result.current.updateFormData({
        player_names: [],
        position_roles: [],
      });
    });

    // Even when trying to validate, should not show position errors with no players
    let isStepValid = false;
    act(() => {
      isStepValid = result.current.validateStep(0);
    });

    expect(result.current.hasFieldError('position_roles')).toBe(false);
  });
});