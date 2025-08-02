import React from 'react';
import { PredictionRequest } from '../types/api';
import { EnhancedPredictionForm } from './enhanced/EnhancedPredictionForm';

interface PredictionFormProps {
  onSubmit: (request: PredictionRequest) => void;
  loading: boolean;
}

export const PredictionForm: React.FC<PredictionFormProps> = ({ onSubmit, loading }) => {
  // Always use enhanced form for better UX - original form is deprecated
  return <EnhancedPredictionForm onSubmit={onSubmit} loading={loading} />;
};