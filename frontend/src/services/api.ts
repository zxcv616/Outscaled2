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
        const apiError = error.response?.data as ApiError;
        throw new Error(apiError?.detail || 'Failed to get prediction');
      }
      throw new Error('Network error');
    }
  },

  async getHealth(): Promise<{ status: string; data_loaded?: boolean }> {
    try {
      const response = await api.get<{ status: string; data_loaded?: boolean }>('/health');
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

  async searchPlayers(query: string, limit: number = 50): Promise<{ players: string[]; total_matches: number }> {
    try {
      const response = await api.get<{ players: string[]; total_matches: number }>('/players/search', {
        params: { q: query, limit }
      });
      return response.data;
    } catch (error) {
      throw new Error('Failed to search players');
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

  async getPlayerDetails(): Promise<{ player_details: Record<string, { position: string | null; team: string | null; games_played: number }> }> {
    try {
      const response = await api.get<{ player_details: Record<string, { position: string | null; team: string | null; games_played: number }> }>('/player-details');
      return response.data;
    } catch (error) {
      throw new Error('Failed to get player details');
    }
  },

  async getOpponents(): Promise<{ opponents: string[] }> {
    try {
      const response = await api.get<{ opponents: string[] }>('/opponents');
      return response.data;
    } catch (error) {
      throw new Error('Failed to get opponents');
    }
  },
}; 