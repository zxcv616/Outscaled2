import { renderHook, act } from '@testing-library/react';
import { usePredictionForm } from '../components/enhanced/hooks/usePredictionForm';

describe('Position Selection Test', () => {
  test('should handle position selection correctly', () => {
    const { result } = renderHook(() => usePredictionForm());

    // Add a player first
    act(() => {
      result.current.updateFormData({
        player_names: ['Ice'],
        position_roles: [''],
      });
    });

    console.log('=== AFTER PLAYER SELECTION ===');
    console.log('Players:', result.current.formData.player_names);
    console.log('Positions:', result.current.formData.position_roles);
    console.log('Position error:', result.current.getFieldError('position_roles'));

    // Now simulate position selection
    act(() => {
      result.current.updateFormData({
        position_roles: ['TOP'],
      });
    });

    console.log('=== AFTER POSITION SELECTION ===');
    console.log('Players:', result.current.formData.player_names);
    console.log('Positions:', result.current.formData.position_roles);
    console.log('Position error:', result.current.getFieldError('position_roles'));

    // Should have no errors after position is selected
    expect(result.current.formData.position_roles).toEqual(['TOP']);
    expect(result.current.hasFieldError('position_roles')).toBe(false);
  });
}); 