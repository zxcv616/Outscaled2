import { renderHook, act } from '@testing-library/react';
import { usePredictionForm } from '../components/enhanced/hooks/usePredictionForm';

describe('Validation Timing Test', () => {
  test('should show validation behavior at each step of user interaction', () => {
    const { result } = renderHook(() => usePredictionForm());

    console.log('=== STEP 1: User adds player Ice (like autocomplete selection) ===');
    
    // This simulates when user selects "Ice" from autocomplete
    // PlayerSelectionStep.handlePlayerChange will create position_roles with empty string
    act(() => {
      result.current.updateFormData({
        player_names: ['Ice'],
        position_roles: [''], // PlayerSelectionStep creates this
      });
    });

    console.log('After adding player:');
    console.log('- Players:', result.current.formData.player_names);
    console.log('- Positions:', result.current.formData.position_roles);
    console.log('- Position error shown:', result.current.hasFieldError('position_roles'));
    console.log('- Error message:', '"' + result.current.getFieldError('position_roles') + '"');

    // At this point, user should NOT see validation error yet
    expect(result.current.hasFieldError('position_roles')).toBe(false);
    console.log('✅ No validation error shown after player selection - GOOD');

    console.log('\n=== STEP 2: User clicks on position dropdown (interaction starts) ===');
    
    // When user clicks position dropdown, onFocus triggers position interaction
    act(() => {
      result.current.markPositionInteractionStarted();
    });

    console.log('After position interaction starts:');
    console.log('- Position error shown:', result.current.hasFieldError('position_roles'));
    console.log('- Error message:', '"' + result.current.getFieldError('position_roles') + '"');

    // Now the question is: should validation error appear when user just focuses the dropdown?
    if (result.current.hasFieldError('position_roles')) {
      console.log('⚠️  Validation error appears when user focuses position dropdown');
      console.log('   This might be too aggressive UX-wise');
    } else {
      console.log('✅ No validation error when user just focuses dropdown - GOOD UX');
    }

    console.log('\n=== STEP 3: User tries to proceed to next step (clicking Next) ===');
    
    // This is when form validation should definitely trigger
    let isStepValid = false;
    act(() => {
      isStepValid = result.current.validateStep(0);
    });

    console.log('After trying to proceed:');
    console.log('- Step valid:', isStepValid);
    console.log('- Position error shown:', result.current.hasFieldError('position_roles'));
    console.log('- Error message:', '"' + result.current.getFieldError('position_roles') + '"');

    // This should definitely show error
    expect(isStepValid).toBe(false);
    expect(result.current.hasFieldError('position_roles')).toBe(true);
    console.log('✅ Validation error shown when trying to proceed - CORRECT');

    console.log('\n=== STEP 4: User selects a position ===');
    
    act(() => {
      result.current.updateFormData({
        position_roles: ['TOP'], // User selects TOP position
      });
    });

    console.log('After selecting position:');
    console.log('- Positions:', result.current.formData.position_roles);
    console.log('- Position error shown:', result.current.hasFieldError('position_roles'));
    console.log('- Error message:', '"' + result.current.getFieldError('position_roles') + '"');

    // Error should clear
    expect(result.current.hasFieldError('position_roles')).toBe(false);
    console.log('✅ Validation error cleared after selecting position - CORRECT');

    console.log('\n=== STEP 5: Validate step again ===');
    
    act(() => {
      isStepValid = result.current.validateStep(0);
    });

    console.log('After final validation:');
    console.log('- Step valid:', isStepValid);
    console.log('- Position error shown:', result.current.hasFieldError('position_roles'));

    expect(isStepValid).toBe(true);
    expect(result.current.hasFieldError('position_roles')).toBe(false);
    console.log('✅ Step valid after proper position selection - CORRECT');
  });

  test('should test if the reported issue is about premature validation', () => {
    const { result } = renderHook(() => usePredictionForm());

    console.log('\n=== REPRODUCING REPORTED ISSUE SCENARIO ===');
    console.log('User report: "Selected Players: Ice" shows validation error immediately');

    // Add player Ice
    act(() => {
      result.current.updateFormData({
        player_names: ['Ice'],
        position_roles: [''],
      });
    });

    console.log('Immediately after adding Ice:');
    console.log('- Shows error:', result.current.hasFieldError('position_roles'));
    
    if (result.current.hasFieldError('position_roles')) {
      console.log('❌ ISSUE CONFIRMED: Validation shows immediately after player selection');
      console.log('   This is likely the UX issue user is reporting');
    } else {
      console.log('✅ No immediate validation - user must be triggering validation somehow');
    }

    // Check if position interaction is being triggered automatically
    console.log('Position interaction started:', result.current.markPositionInteractionStarted);

    // Let's see what happens if we trigger position validation directly
    const positionError = result.current.validateField('position_roles', [''], 0);
    console.log('Direct position validation result:', '"' + positionError + '"');

    if (positionError) {
      console.log('   This is the exact message user is seeing');
    }
  });
});