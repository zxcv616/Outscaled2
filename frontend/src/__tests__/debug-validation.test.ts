import { renderHook, act } from '@testing-library/react';
import { usePredictionForm } from '../components/enhanced/hooks/usePredictionForm';

describe('Validation Issue Debug Test', () => {
  test('should reproduce the exact validation behavior from Docker', () => {
    const { result } = renderHook(() => usePredictionForm());

    console.log('=== INITIAL STATE ===');
    console.log('Players:', result.current.formData.player_names);
    console.log('Positions:', result.current.formData.position_roles);
    console.log('Position error:', result.current.getFieldError('position_roles'));
    console.log('Has position error:', result.current.hasFieldError('position_roles'));

    // Step 1: Add player "Ice" like in the reported issue
    act(() => {
      result.current.updateFormData({
        player_names: ['Ice'],
      });
    });

    console.log('=== AFTER ADDING PLAYER "Ice" ===');
    console.log('Players:', result.current.formData.player_names);
    console.log('Positions:', result.current.formData.position_roles);
    console.log('Position error:', result.current.getFieldError('position_roles'));
    console.log('Has position error:', result.current.hasFieldError('position_roles'));

    // At this point, no error should be shown
    expect(result.current.hasFieldError('position_roles')).toBe(false);

    // Step 2: Simulate what happens when trying to validate step (like clicking next)
    let isStepValid = false;
    act(() => {
      isStepValid = result.current.validateStep(0);
    });

    console.log('=== AFTER VALIDATE STEP ===');
    console.log('Step valid:', isStepValid);
    console.log('Players:', result.current.formData.player_names);
    console.log('Positions:', result.current.formData.position_roles);
    console.log('Position error:', result.current.getFieldError('position_roles'));
    console.log('Has position error:', result.current.hasFieldError('position_roles'));

    // Now it should show an error since we tried to validate
    expect(isStepValid).toBe(false);
    expect(result.current.hasFieldError('position_roles')).toBe(true);
    
    // Check if the error message matches what was reported
    const errorMessage = result.current.getFieldError('position_roles');
    console.log('=== ACTUAL ERROR MESSAGE ===');
    console.log('"' + errorMessage + '"');
    
    // The user reported: "Please select a position for all players (1 position not assigned)"
    // Let's see what we actually get
    expect(errorMessage).toContain('position');
    expect(errorMessage).toContain('not assigned');
    
    // Let's also test with positions array initialized but empty
    act(() => {
      result.current.updateFormData({
        position_roles: [''],
      });
    });

    console.log('=== AFTER ADDING EMPTY POSITION ===');
    console.log('Players:', result.current.formData.player_names);
    console.log('Positions:', result.current.formData.position_roles);
    console.log('Position error:', result.current.getFieldError('position_roles'));
    console.log('Has position error:', result.current.hasFieldError('position_roles'));

    // Validate again
    act(() => {
      isStepValid = result.current.validateStep(0);
    });

    console.log('=== FINAL VALIDATION ===');
    console.log('Step valid:', isStepValid);
    console.log('Position error:', result.current.getFieldError('position_roles'));
    
    const finalErrorMessage = result.current.getFieldError('position_roles');
    console.log('=== FINAL ERROR MESSAGE ===');
    console.log('"' + finalErrorMessage + '"');
  });

  test('should test old vs new validation message format', () => {
    const { result } = renderHook(() => usePredictionForm());

    // Add player and trigger validation
    act(() => {
      result.current.updateFormData({
        player_names: ['Ice'],
        position_roles: [''],
      });
    });

    act(() => {
      result.current.validateStep(0);
    });

    const errorMessage = result.current.getFieldError('position_roles');
    console.log('=== VALIDATION MESSAGE ANALYSIS ===');
    console.log('Message:', '"' + errorMessage + '"');
    console.log('Contains "not assigned":', errorMessage.includes('not assigned'));
    console.log('Contains "remaining player":', errorMessage.includes('remaining player'));
    console.log('Contains number of players:', errorMessage.includes('1'));
    
    // If it contains old format, we know the issue
    if (errorMessage.includes('remaining player')) {
      console.log('❌ OLD VALIDATION FORMAT DETECTED');
    } else {
      console.log('✅ NEW VALIDATION FORMAT DETECTED');
    }
  });
});