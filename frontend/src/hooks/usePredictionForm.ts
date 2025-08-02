import { useState, useEffect, useCallback } from 'react';
import { PredictionRequest } from '../types/api';
import { predictionApi } from '../services/api';

export interface FormStep {
  id: string;
  title: string;
  description: string;
  fields: string[];
  isValid: boolean;
}

export interface PredictionFormState {
  player_names: string[];
  prop_type: 'kills' | 'assists';
  prop_value: number;
  map_range: [number, number];
  opponent: string;
  tournament: string;
  team: string;
  match_date: string;
  position_roles: string[];
  strict_mode: boolean;
}

export interface FormErrors {
  [key: string]: string;
}

export interface FormLoadingStates {
  players: boolean;
  teams: boolean;
  tournaments: boolean;
  validation: boolean;
}

const initialFormState: PredictionFormState = {
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
};

const formSteps: FormStep[] = [
  {
    id: 'players',
    title: 'Player Selection',
    description: 'Choose the players for your prediction',
    fields: ['player_names', 'position_roles'],
    isValid: false,
  },
  {
    id: 'match-details',
    title: 'Match Details',
    description: 'Set up the match context',
    fields: ['team', 'opponent', 'tournament', 'match_date'],
    isValid: false,
  },
  {
    id: 'prop-settings',
    title: 'Prop Configuration',
    description: 'Configure your prop bet parameters',
    fields: ['prop_type', 'prop_value', 'map_range', 'strict_mode'],
    isValid: false,
  },
];

export const usePredictionForm = () => {
  const [formData, setFormData] = useState<PredictionFormState>(initialFormState);
  const [errors, setErrors] = useState<FormErrors>({});
  const [currentStep, setCurrentStep] = useState(0);
  const [steps, setSteps] = useState<FormStep[]>(formSteps);
  const [loading, setLoading] = useState<FormLoadingStates>({
    players: true,
    teams: true,
    tournaments: true,
    validation: false,
  });

  // Available options from API
  const [availablePlayers, setAvailablePlayers] = useState<string[]>([]);
  const [availableTeams, setAvailableTeams] = useState<string[]>([]);
  const [availableTournaments, setAvailableTournaments] = useState<string[]>([]);

  // Load initial data
  useEffect(() => {
    const loadData = async () => {
      try {
        const [playersResponse, teamsResponse, tournamentsResponse] = await Promise.all([
          predictionApi.getPlayers(),
          predictionApi.getTeams(),
          predictionApi.getTournaments()
        ]);
        
        setAvailablePlayers(playersResponse.players);
        setAvailableTeams(teamsResponse.teams);
        setAvailableTournaments(tournamentsResponse.tournaments);
        
        // Set default tournament
        if (tournamentsResponse.tournaments.length > 0) {
          setFormData(prev => ({ 
            ...prev, 
            tournament: tournamentsResponse.tournaments[0] 
          }));
        }
      } catch (error) {
        console.error('Failed to load form data:', error);
      } finally {
        setLoading(prev => ({
          ...prev,
          players: false,
          teams: false,
          tournaments: false,
        }));
      }
    };

    loadData();
  }, []);

  // Validation functions
  const validateField = useCallback((field: string, value: any): string => {
    switch (field) {
      case 'player_names':
        return value?.length === 0 ? 'At least one player is required' : '';
      case 'prop_value':
        return !value || value <= 0 ? 'Prop value must be greater than 0' : '';
      case 'opponent':
        return !value ? 'Opponent is required' : '';
      case 'position_roles':
        return value?.length === 0 ? 'At least one position is required' : '';
      case 'tournament':
        return !value ? 'Tournament is required' : '';
      default:
        return '';
    }
  }, []);

  const validateStep = useCallback((stepIndex: number): boolean => {
    const step = steps[stepIndex];
    const stepErrors: FormErrors = {};
    let isValid = true;

    step.fields.forEach(field => {
      const error = validateField(field, formData[field as keyof PredictionFormState]);
      if (error) {
        stepErrors[field] = error;
        isValid = false;
      }
    });

    setErrors(prev => ({ ...prev, ...stepErrors }));
    
    // Update step validity
    setSteps(prev => prev.map((s, i) => 
      i === stepIndex ? { ...s, isValid } : s
    ));

    return isValid;
  }, [formData, steps, validateField]);

  // Real-time validation with debouncing
  useEffect(() => {
    const timer = setTimeout(() => {
      validateStep(currentStep);
    }, 300);

    return () => clearTimeout(timer);
  }, [formData, currentStep, validateStep]);

  const updateField = useCallback((field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error for this field
    setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[field];
      return newErrors;
    });
  }, []);

  const nextStep = useCallback(() => {
    if (currentStep < steps.length - 1 && validateStep(currentStep)) {
      setCurrentStep(prev => prev + 1);
    }
  }, [currentStep, steps.length, validateStep]);

  const prevStep = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  }, [currentStep]);

  const goToStep = useCallback((stepIndex: number) => {
    if (stepIndex >= 0 && stepIndex < steps.length) {
      setCurrentStep(stepIndex);
    }
  }, [steps.length]);

  const canSubmit = useCallback(() => {
    return steps.every(step => step.isValid);
  }, [steps]);

  const getFormRequest = useCallback((): PredictionRequest => {
    return {
      player_names: formData.player_names,
      prop_type: formData.prop_type,
      prop_value: formData.prop_value,
      map_range: formData.map_range,
      opponent: formData.opponent,
      tournament: formData.tournament,
      team: formData.team && formData.team.trim() ? formData.team : undefined,
      match_date: formData.match_date,
      position_roles: formData.position_roles,
      strict_mode: formData.strict_mode,
    };
  }, [formData]);

  const resetForm = useCallback(() => {
    setFormData(initialFormState);
    setErrors({});
    setCurrentStep(0);
    setSteps(formSteps.map(step => ({ ...step, isValid: false })));
  }, []);

  return {
    // Form state
    formData,
    errors,
    currentStep,
    steps,
    loading,
    
    // Available options
    availablePlayers,
    availableTeams,
    availableTournaments,
    
    // Actions
    updateField,
    nextStep,
    prevStep,
    goToStep,
    validateStep,
    canSubmit,
    getFormRequest,
    resetForm,
    
    // Computed properties
    isFirstStep: currentStep === 0,
    isLastStep: currentStep === steps.length - 1,
    currentStepData: steps[currentStep],
    progressPercentage: ((currentStep + 1) / steps.length) * 100,
  };
};