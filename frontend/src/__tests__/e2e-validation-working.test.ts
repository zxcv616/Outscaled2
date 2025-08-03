/**
 * END-TO-END VALIDATION TEST - CURRENT WORKING STATE
 * 
 * This test validates that the simplified single player/position form works correctly
 * after the recent validation fixes. Tests the actual user flow from start to completion.
 */

import { renderHook, act } from '@testing-library/react';
import { usePredictionForm } from '../components/enhanced/hooks/usePredictionForm';

describe('E2E Validation - Current Working State', () => {
  describe('Single Player Form Flow', () => {
    test('should handle complete user flow without premature validation errors', () => {
      console.log('\n🚀 E2E TEST: Complete Single Player Form Flow');
      console.log('====================================================');
      
      const { result } = renderHook(() => usePredictionForm());

      // STEP 1: Initial state should have no errors
      console.log('\n📋 STEP 1: Initial State Check');
      expect(result.current.hasFieldError('player_names')).toBe(false);
      expect(result.current.hasFieldError('position_roles')).toBe(false);
      expect(result.current.formData.player_names).toEqual([]);
      expect(result.current.formData.position_roles).toEqual([]);
      console.log('✅ Initial state clean - no errors, empty arrays');

      // STEP 2: Add a player (simulates autocomplete selection)
      console.log('\n👤 STEP 2: Player Selection');
      act(() => {
        result.current.updateFormData({
          player_names: ['Faker'],
          position_roles: [''], // PlayerSelectionStep creates empty position slot
        });
      });

      console.log('After player selection:');
      console.log('- Players:', result.current.formData.player_names);
      console.log('- Positions:', result.current.formData.position_roles);
      console.log('- Has player error:', result.current.hasFieldError('player_names'));
      console.log('- Has position error:', result.current.hasFieldError('position_roles'));

      // Critical: No validation errors should appear immediately after player selection
      expect(result.current.hasFieldError('player_names')).toBe(false);
      expect(result.current.hasFieldError('position_roles')).toBe(false);
      console.log('✅ No premature validation errors after player selection');

      // STEP 3: Position auto-suggestion (simulates auto-suggest for Faker -> MID)
      console.log('\n⚡ STEP 3: Position Auto-Suggestion');
      act(() => {
        result.current.updateFormData({
          position_roles: ['MID'], // Auto-suggested position
        });
      });

      console.log('After position auto-suggestion:');
      console.log('- Positions:', result.current.formData.position_roles);
      console.log('- Has position error:', result.current.hasFieldError('position_roles'));

      expect(result.current.hasFieldError('position_roles')).toBe(false);
      console.log('✅ Position auto-suggestion works without errors');

      // STEP 4: Check step validity (UI state checks)
      console.log('\n🔍 STEP 4: Step Validity Checks (UI State)');
      const isStep0Valid = result.current.isStepValid(0);
      console.log('- isStepValid(0):', isStep0Valid);
      console.log('- Has position error after validity check:', result.current.hasFieldError('position_roles'));

      expect(isStep0Valid).toBe(true);
      expect(result.current.hasFieldError('position_roles')).toBe(false);
      console.log('✅ Step validity check works correctly');

      // STEP 5: Form completion check
      console.log('\n✅ STEP 5: Form Completion Check');
      const isFormComplete = result.current.isFormComplete();
      console.log('- isFormComplete():', isFormComplete);

      expect(isFormComplete).toBe(true);
      console.log('✅ Form completion validation works');

      // STEP 6: Final validation before submission
      console.log('\n🚀 STEP 6: Final Validation');
      let finalValidation = false;
      act(() => {
        finalValidation = result.current.validateStep(0);
      });

      console.log('- Final validation result:', finalValidation);
      console.log('- Any errors after final validation:', {
        player_names: result.current.getFieldError('player_names'),
        position_roles: result.current.getFieldError('position_roles')
      });

      expect(finalValidation).toBe(true);
      expect(result.current.hasFieldError('player_names')).toBe(false);
      expect(result.current.hasFieldError('position_roles')).toBe(false);
      console.log('✅ Final validation passes - ready for submission');
    });

    test('should show validation errors only when user tries to proceed with incomplete form', () => {
      console.log('\n⚠️  E2E TEST: Validation Error Timing');
      console.log('====================================');
      
      const { result } = renderHook(() => usePredictionForm());

      // Add player but leave position empty
      act(() => {
        result.current.updateFormData({
          player_names: ['Ice'],
          position_roles: [''], // Empty position
        });
      });

      console.log('After adding player with empty position:');
      console.log('- Has position error:', result.current.hasFieldError('position_roles'));
      
      expect(result.current.hasFieldError('position_roles')).toBe(false);
      console.log('✅ No error shown immediately');

      // Now try to validate step (like clicking Next)
      console.log('\nUser tries to proceed to next step:');
      let stepValid = false;
      act(() => {
        stepValid = result.current.validateStep(0);
      });

      console.log('- Step valid:', stepValid);
      console.log('- Position error:', result.current.getFieldError('position_roles'));
      console.log('- Has position error:', result.current.hasFieldError('position_roles'));

      expect(stepValid).toBe(false);
      expect(result.current.hasFieldError('position_roles')).toBe(true);
      expect(result.current.getFieldError('position_roles')).toBe('Please select a position for the player');
      console.log('✅ Validation error appears only when user tries to proceed');
    });

    test('should handle position changes correctly', () => {
      console.log('\n🎯 E2E TEST: Position Change Handling');
      console.log('====================================');
      
      const { result } = renderHook(() => usePredictionForm());

      // Setup: Add player with empty position
      act(() => {
        result.current.updateFormData({
          player_names: ['Caps'],
          position_roles: [''],
        });
      });

      console.log('Initial setup - player with empty position:');
      console.log('- Players:', result.current.formData.player_names);
      console.log('- Positions:', result.current.formData.position_roles);

      // User selects a position
      act(() => {
        result.current.updateFormData({
          position_roles: ['MID'],
        });
      });

      console.log('After position selection:');
      console.log('- Positions:', result.current.formData.position_roles);
      console.log('- Position error:', result.current.getFieldError('position_roles'));

      expect(result.current.hasFieldError('position_roles')).toBe(false);
      expect(result.current.formData.position_roles[0]).toBe('MID');
      console.log('✅ Position change handled correctly');

      // User changes to different position
      act(() => {
        result.current.updateFormData({
          position_roles: ['TOP'],
        });
      });

      console.log('After position change:');
      console.log('- Positions:', result.current.formData.position_roles);

      expect(result.current.formData.position_roles[0]).toBe('TOP');
      console.log('✅ Position change works correctly');

      // Final validation should pass
      let finalValid = false;
      act(() => {
        finalValid = result.current.validateStep(0);
      });

      expect(finalValid).toBe(true);
      console.log('✅ Final validation passes after position change');
    });
  });

  describe('Form State Management', () => {
    test('should maintain consistent state through all operations', () => {
      console.log('\n🔄 E2E TEST: State Consistency');
      console.log('==============================');
      
      const { result } = renderHook(() => usePredictionForm());

      // Track all state changes
      const stateChanges: any[] = [];
      
      const captureState = (label: string) => {
        const state = {
          label,
          players: [...result.current.formData.player_names],
          positions: [...result.current.formData.position_roles],
          errors: {
            players: result.current.getFieldError('player_names'),
            positions: result.current.getFieldError('position_roles')
          }
        };
        stateChanges.push(state);
        console.log(`${label}:`, state);
      };

      captureState('Initial');

      act(() => {
        result.current.updateFormData({
          player_names: ['Bjergsen'],
          position_roles: [''],
        });
      });
      captureState('After Player Add');

      act(() => {
        result.current.updateFormData({
          position_roles: ['MID'],
        });
      });
      captureState('After Position Select');

      act(() => {
        result.current.validateStep(0);
      });
      captureState('After Validation');

      // Verify state consistency
      const finalState = stateChanges[stateChanges.length - 1];
      expect(finalState.players).toEqual(['Bjergsen']);
      expect(finalState.positions).toEqual(['MID']);
      expect(finalState.errors.players).toBe('');
      expect(finalState.errors.positions).toBe('');
      
      console.log('✅ State remains consistent through all operations');
    });
  });

  describe('Edge Cases', () => {
    test('should handle rapid state changes gracefully', () => {
      console.log('\n⚡ E2E TEST: Rapid State Changes');
      console.log('================================');
      
      const { result } = renderHook(() => usePredictionForm());

      // Simulate rapid user interactions
      act(() => {
        result.current.updateFormData({
          player_names: ['Player1'],
          position_roles: [''],
        });
      });

      act(() => {
        result.current.updateFormData({
          player_names: ['Player2'],
          position_roles: ['TOP'],
        });
      });

      act(() => {
        result.current.updateFormData({
          position_roles: ['MID'],
        });
      });

      act(() => {
        result.current.updateFormData({
          player_names: ['FinalPlayer'],
        });
      });

      console.log('Final state after rapid changes:');
      console.log('- Players:', result.current.formData.player_names);
      console.log('- Positions:', result.current.formData.position_roles);

      expect(result.current.formData.player_names).toEqual(['FinalPlayer']);
      expect(result.current.formData.position_roles).toEqual(['MID']);
      expect(result.current.hasFieldError('player_names')).toBe(false);
      expect(result.current.hasFieldError('position_roles')).toBe(false);
      
      console.log('✅ Rapid state changes handled gracefully');
    });

    test('should handle empty string vs empty array edge cases', () => {
      console.log('\n🔍 E2E TEST: Empty Value Edge Cases');
      console.log('====================================');
      
      const { result } = renderHook(() => usePredictionForm());

      // Test empty string position
      act(() => {
        result.current.updateFormData({
          player_names: ['TestPlayer'],
          position_roles: [''], // Empty string
        });
      });

      console.log('Empty string position:');
      console.log('- Position value:', JSON.stringify(result.current.formData.position_roles));
      console.log('- Has error:', result.current.hasFieldError('position_roles'));

      expect(result.current.hasFieldError('position_roles')).toBe(false);

      // Test validation with empty string
      act(() => {
        result.current.validateStep(0);
      });

      expect(result.current.hasFieldError('position_roles')).toBe(true);
      console.log('✅ Empty string position triggers validation error when needed');

      // Test with actual position value
      act(() => {
        result.current.updateFormData({
          position_roles: ['JNG'],
        });
      });

      act(() => {
        result.current.validateStep(0);
      });

      expect(result.current.hasFieldError('position_roles')).toBe(false);
      console.log('✅ Valid position clears validation error');
    });
  });
});