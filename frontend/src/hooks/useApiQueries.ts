import { useQuery, useQueryClient } from '@tanstack/react-query';
import { predictionApi } from '../services/api';

// Query keys for consistent caching
export const queryKeys = {
  players: ['players'] as const,
  playerSearch: (query: string) => ['players', 'search', query] as const,
  teams: ['teams'] as const,
  tournaments: ['tournaments'] as const,
  opponents: ['opponents'] as const,
  playerDetails: ['playerDetails'] as const,
} as const;

// Players search query with debouncing built into TanStack Query
export function usePlayerSearch(query: string) {
  return useQuery({
    queryKey: queryKeys.playerSearch(query),
    queryFn: () => predictionApi.searchPlayers(query, 50),
    enabled: query.length >= 2, // Only run if query is 2+ characters
    staleTime: 5 * 60 * 1000, // 5 minutes
    placeholderData: { players: [], total_matches: 0 }, // Show empty state while loading
  });
}

// Teams query
export function useTeams() {
  return useQuery({
    queryKey: queryKeys.teams,
    queryFn: predictionApi.getTeams,
    staleTime: 30 * 60 * 1000, // 30 minutes (teams don't change often)
  });
}

// Tournaments query
export function useTournaments() {
  return useQuery({
    queryKey: queryKeys.tournaments,
    queryFn: predictionApi.getTournaments,
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
}

// Opponents query
export function useOpponents() {
  return useQuery({
    queryKey: queryKeys.opponents,
    queryFn: predictionApi.getOpponents,
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
}

// Player details query
export function usePlayerDetails() {
  return useQuery({
    queryKey: queryKeys.playerDetails,
    queryFn: predictionApi.getPlayerDetails,
    staleTime: 15 * 60 * 1000, // 15 minutes
  });
}

// Health check query
export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: predictionApi.getHealth,
    staleTime: 1 * 60 * 1000, // 1 minute
    retry: 1, // Don't retry health checks too much
  });
}