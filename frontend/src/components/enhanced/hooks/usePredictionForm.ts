import { useState, useCallback, useMemo } from 'react';
import { PredictionRequest } from '../../../types/api';

interface FormData extends Partial<PredictionRequest> {
  // Enhanced form state with validation tracking
}

interface FormErrors {
  [key: string]: string;
}

interface ValidationRules {
  [stepIndex: number]: {
    [fieldName: string]: (value: any, formData: FormData) => string | null;
  };
}

export const usePredictionForm = () => {
  const [formData, setFormData] = useState<FormData>({
    player_names: [],
    prop_type: 'kills',
    prop_value: 0,
    map_range: [1, 2],
    opponent: '',
    tournament: '',
    team: '',
    match_date: new Date().toISOString().slice(0, 16),
    position_roles: [],
    strict_mode: false,
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [touchedFields, setTouchedFields] = useState<Set<string>>(new Set());
  const [positionInteractionStarted, setPositionInteractionStarted] = useState(false);

  // Validation rules for each step
  const validationRules: ValidationRules = useMemo(() => ({
    0: { // Player Selection Step
      player_names: (value: string[]) => {
        if (!value || value.length === 0) {
          return 'At least one player is required';
        }
        if (value.length > 5) {
          return 'Maximum 5 players allowed';
        }
        return null;
      },
      position_roles: (value: string[], formData: FormData) => {
        // Only validate positions if players are selected
        if (!formData.player_names || formData.player_names.length === 0) {
          return null; // No validation needed if no players selected yet
        }
        
        // Don't show validation errors until user has started interacting with positions
        // or when trying to progress to the next step
        if (!positionInteractionStarted && !touchedFields.has('position_roles')) {
          return null;
        }
        
        if (!value || value.length === 0) {
          return `Please assign positions for your ${formData.player_names.length} player${formData.player_names.length > 1 ? 's' : ''}`;
        }
        
        if (value.length !== formData.player_names.length) {
          return `Number of positions (${value.length}) must match number of players (${formData.player_names.length})`;
        }
        
        // Check for empty position slots
        const emptyPositions = value.filter((pos: string) => !pos || pos.trim() === '').length;
        if (emptyPositions > 0) {
          return `Please select a position for all players (${emptyPositions} position${emptyPositions > 1 ? 's' : ''} not assigned)`;
        }
        
        return null;
      },
    },
    1: { // Match Details Step
      tournament: (value: string) => {
        if (!value || value.trim() === '') {
          return 'Tournament is required';
        }
        return null;
      },
      opponent: (value: string) => {
        if (!value || value.trim() === '') {
          return 'Opponent team is required';
        }
        return null;
      },
      match_date: (value: string) => {
        if (!value) {
          return 'Match date is required';
        }
        const date = new Date(value);
        const now = new Date();
        if (date < new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000)) {
          return 'Match date cannot be more than a year in the past';
        }
        return null;
      },
    },
    2: { // Prop Configuration Step
      prop_type: (value: string) => {
        if (!value || !['kills', 'assists'].includes(value)) {
          return 'Valid prop type is required';
        }
        return null;
      },
      prop_value: (value: number) => {
        if (!value || value <= 0) {
          return 'Prop value must be greater than 0';
        }
        if (value > 50) {
          return 'Prop value seems unrealistic (max 50)';
        }
        return null;
      },
      map_range: (value: [number, number]) => {
        if (!value || value.length !== 2) {
          return 'Map range is required';
        }
        if (value[0] < 1 || value[1] < 1 || value[0] > 5 || value[1] > 5) {
          return 'Map numbers must be between 1 and 5';
        }
        if (value[0] > value[1]) {
          return 'Start map must be less than or equal to end map';
        }
        return null;
      },
    },
  }), [positionInteractionStarted, touchedFields]);

  const validateField = useCallback((fieldName: string, value: any, stepIndex?: number): string | null => {
    if (stepIndex !== undefined) {
      const stepRules = validationRules[stepIndex];
      if (stepRules && stepRules[fieldName]) {
        return stepRules[fieldName](value, formData);
      }
    }

    // Find field in any step if stepIndex not provided
    for (const step of Object.values(validationRules)) {
      if (step[fieldName]) {
        return step[fieldName](value, formData);
      }
    }

    return null;
  }, [formData, validationRules]);

  const validateStep = useCallback((stepIndex: number): boolean => {
    const stepRules = validationRules[stepIndex];
    if (!stepRules) return true;

    // Force position interaction tracking when validating step 0
    if (stepIndex === 0 && !positionInteractionStarted) {
      setPositionInteractionStarted(true);
    }

    const stepErrors: FormErrors = {};
    let isValid = true;

    Object.entries(stepRules).forEach(([fieldName, validator]) => {
      const value = formData[fieldName as keyof FormData];
      const error = validator(value, formData);
      if (error) {
        stepErrors[fieldName] = error;
        isValid = false;
      }
    });

    setErrors(prev => ({
      ...prev,
      ...stepErrors,
    }));

    return isValid;
  }, [formData, validationRules, positionInteractionStarted]);

  const isStepValid = useCallback((stepIndex: number): boolean => {
    const stepRules = validationRules[stepIndex];
    if (!stepRules) return true;

    return Object.entries(stepRules).every(([fieldName, validator]) => {
      const value = formData[fieldName as keyof FormData];
      return validator(value, formData) === null;
    });
  }, [formData, validationRules]);

  const isFormComplete = useCallback((): boolean => {
    return [0, 1, 2].every(stepIndex => isStepValid(stepIndex));
  }, [isStepValid]);

  const updateFormData = useCallback((updates: Partial<FormData>) => {
    // Track when user starts interacting with positions
    if (updates.position_roles && !positionInteractionStarted) {
      setPositionInteractionStarted(true);
    }

    setFormData(prev => {
      const newData = { ...prev, ...updates };
      
      // Real-time validation for touched fields
      const newErrors: FormErrors = {};
      Object.keys(updates).forEach(fieldName => {
        if (touchedFields.has(fieldName) || (fieldName === 'position_roles' && positionInteractionStarted)) {
          const error = validateField(fieldName, newData[fieldName as keyof FormData]);
          if (error) {
            newErrors[fieldName] = error;
          }
        }
      });

      setErrors(prev => ({
        ...prev,
        ...newErrors,
        // Clear errors for updated fields that are now valid
        ...Object.keys(updates).reduce((acc, fieldName) => {
          if (!newErrors[fieldName]) {
            acc[fieldName] = '';
          }
          return acc;
        }, {} as FormErrors),
      }));

      return newData;
    });

    // Mark fields as touched
    setTouchedFields(prev => new Set([...Array.from(prev), ...Object.keys(updates)]));
  }, [touchedFields, validateField, positionInteractionStarted]);

  const submitForm = useCallback((onSubmit: (request: PredictionRequest) => void) => {
    if (!isFormComplete()) {
      // Validate all steps to show all errors
      [0, 1, 2].forEach(stepIndex => validateStep(stepIndex));
      return;
    }

    // Convert form data to API request format
    const request: PredictionRequest = {
      player_names: formData.player_names!,
      prop_type: formData.prop_type as 'kills' | 'assists',
      prop_value: formData.prop_value!,
      map_range: formData.map_range as [number, number],
      opponent: formData.opponent!,
      tournament: formData.tournament!,
      team: formData.team && formData.team.trim() ? formData.team : undefined,
      match_date: formData.match_date!,
      position_roles: formData.position_roles!,
      strict_mode: formData.strict_mode || false,
    };

    onSubmit(request);
  }, [formData, isFormComplete, validateStep]);

  const resetForm = useCallback(() => {
    setFormData({
      player_names: [],
      prop_type: 'kills',
      prop_value: 0,
      map_range: [1, 2],
      opponent: '',
      tournament: '',
      team: '',
      match_date: new Date().toISOString().slice(0, 16),
      position_roles: [],
      strict_mode: false,
    });
    setErrors({});
    setTouchedFields(new Set());
    setPositionInteractionStarted(false);
  }, []);

  const getFieldError = useCallback((fieldName: string): string => {
    return errors[fieldName] || '';
  }, [errors]);

  const hasFieldError = useCallback((fieldName: string): boolean => {
    return Boolean(errors[fieldName]);
  }, [errors]);

  const markPositionInteractionStarted = useCallback(() => {
    if (!positionInteractionStarted) {
      setPositionInteractionStarted(true);
    }
  }, [positionInteractionStarted]);

  return {
    formData,
    errors,
    touchedFields,
    updateFormData,
    validateStep,
    isStepValid,
    isFormComplete,
    submitForm,
    resetForm,
    getFieldError,
    hasFieldError,
    validateField,
    markPositionInteractionStarted,
  };
};