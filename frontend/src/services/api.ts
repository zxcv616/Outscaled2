import axios from 'axios';
import { PredictionRequest, PredictionResponse, ApiError } from '../types/api';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const predictionApi = {
  async getPrediction(request: PredictionRequest): Promise<PredictionResponse> {
    try {
      const response = await api.post<PredictionResponse>('/predict', request);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        // Handle different types of axios errors
        if (error.response) {
          // Server responded with error status
          const apiError = error.response.data as ApiError;
          
          // Handle different error formats
          let errorMessage = '';
          if (apiError?.detail) {
            if (Array.isArray(apiError.detail)) {
              // Handle validation errors with multiple details
              errorMessage = apiError.detail.map((detail: any) => 
                `${detail.loc?.join('.')}: ${detail.msg}`
              ).join(', ');
            } else {
              errorMessage = apiError.detail;
            }
          } else if (apiError?.message) {
            errorMessage = apiError.message;
          } else {
            errorMessage = `Server error: ${error.response.status}`;
          }
          
          throw new Error(errorMessage);
        } else if (error.request) {
          // Request was made but no response received
          throw new Error('No response from server. Please check your connection.');
        } else {
          // Something else happened
          throw new Error('Network error occurred');
        }
      }
      // Handle non-axios errors
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred');
    }
  },

  async getHealth(): Promise<{ status: string }> {
    try {
      const response = await api.get<{ status: string }>('/health');
      return response.data;
    } catch (error) {
      throw new Error('Health check failed');
    }
  },

  async getPlayers(): Promise<{ players: string[] }> {
    try {
      const response = await api.get<{ players: string[] }>('/players');
      return response.data;
    } catch (error) {
      throw new Error('Failed to get players');
    }
  },

  async getTeams(): Promise<{ teams: string[] }> {
    try {
      const response = await api.get<{ teams: string[] }>('/teams');
      return response.data;
    } catch (error) {
      throw new Error('Failed to get teams');
    }
  },

  async getTournaments(): Promise<{ tournaments: string[] }> {
    try {
      const response = await api.get<{ tournaments: string[] }>('/tournaments');
      return response.data;
    } catch (error) {
      throw new Error('Failed to get tournaments');
    }
  },
}; 