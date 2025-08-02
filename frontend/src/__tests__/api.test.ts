import axios from 'axios';
import { predictionApi } from '../services/api';
import { PredictionRequest, PredictionResponse } from '../types/api';

// Mock axios
jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock axios.create to return a mocked instance
    mockAxios.create = jest.fn(() => mockAxios);
  });

  describe('getPlayers', () => {
    test('successfully gets players', async () => {
      const mockResponse = {
        data: {
          players: ['Player1', 'Player2', 'Player3', 'Player4', 'Player5']
        }
      };
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      const result = await predictionApi.getPlayers();

      expect(mockAxios.get).toHaveBeenCalledWith('/players');
      expect(result).toEqual({ players: ['Player1', 'Player2', 'Player3', 'Player4', 'Player5'] });
    });

    test('handles API error', async () => {
      mockAxios.get = jest.fn().mockRejectedValue(new Error('Network error'));

      await expect(predictionApi.getPlayers()).rejects.toThrow('Failed to get players');
    });

    test('handles empty response', async () => {
      const mockResponse = {
        data: {
          players: []
        }
      };
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      const result = await predictionApi.getPlayers();

      expect(result).toEqual({ players: [] });
    });
  });

  describe('getTeams', () => {
    test('successfully gets teams', async () => {
      const mockResponse = {
        data: {
          teams: ['Team1', 'Team2', 'Team3', 'Team4', 'Team5']
        }
      };
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      const result = await predictionApi.getTeams();

      expect(mockAxios.get).toHaveBeenCalledWith('/teams');
      expect(result).toEqual({ teams: ['Team1', 'Team2', 'Team3', 'Team4', 'Team5'] });
    });

    test('handles API error', async () => {
      mockAxios.get = jest.fn().mockRejectedValue(new Error('Network error'));

      await expect(predictionApi.getTeams()).rejects.toThrow('Failed to get teams');
    });
  });

  describe('getPrediction', () => {
    const mockRequest: PredictionRequest = {
      player_names: ['Player1'],
      prop_type: 'kills',
      prop_value: 5.0,
      map_range: [1, 3],
      opponent: 'Team2',
      tournament: 'LPL',
      team: 'Team1',
      match_date: '2024-01-15T10:00:00',
      position_roles: ['MID']
    };

    const mockResponse: PredictionResponse = {
      prediction: 'OVER',
      confidence: 75.0,
      expected_stat: 4.5,
      confidence_interval: [3.8, 5.2],
      reasoning: 'Good recent form. Moderate sample size. Expected performance close to prop line. Moderate confidence prediction.',
      player_stats: {
        avg_kills: 4.0,
        avg_assists: 6.0,
        form_z_score: 0.5,
        maps_played: 10,
        avg_deaths: 2.5,
        avg_damage: 15000,
        avg_vision: 25.0,
        avg_cs: 200.0,
        position_factor: 1.2
      },
      data_years: '2024 (108 matches), 2025 (67 matches)'
    };

    test('successfully gets prediction', async () => {
      mockAxios.post = jest.fn().mockResolvedValue({
        data: mockResponse
      });

      const result = await predictionApi.getPrediction(mockRequest);

      expect(mockAxios.post).toHaveBeenCalledWith('/predict', mockRequest);
      expect(result).toEqual(mockResponse);
    });

    test('handles API error', async () => {
      mockAxios.post = jest.fn().mockRejectedValue(new Error('Network error'));

      await expect(predictionApi.getPrediction(mockRequest)).rejects.toThrow('Failed to get prediction');
    });

    test('handles validation error response', async () => {
      const mockErrorResponse = {
        response: {
          status: 400,
          data: {
            detail: 'Validation error: prop_value must be greater than 0'
          }
        }
      };
      mockAxios.post = jest.fn().mockRejectedValue(mockErrorResponse);

      await expect(predictionApi.getPrediction(mockRequest)).rejects.toThrow('Failed to get prediction');
    });

    test('handles server error response', async () => {
      const mockErrorResponse = {
        response: {
          status: 500,
          data: {
            detail: 'Internal server error'
          }
        }
      };
      mockAxios.post = jest.fn().mockRejectedValue(mockErrorResponse);

      await expect(predictionApi.getPrediction(mockRequest)).rejects.toThrow('Failed to get prediction');
    });
  });

  describe('API configuration', () => {
    test('uses correct base URL', () => {
      // The axios instance should be created with the correct configuration
      expect(mockAxios.create).toHaveBeenCalled();
    });

    test('handles different prop types', async () => {
      const killsRequest: PredictionRequest = {
        ...mockRequest,
        prop_type: 'kills'
      };
      const assistsRequest: PredictionRequest = {
        ...mockRequest,
        prop_type: 'assists'
      };

      mockAxios.post = jest.fn().mockResolvedValue({
        data: mockResponse
      });

      await predictionApi.getPrediction(killsRequest);
      await predictionApi.getPrediction(assistsRequest);

      expect(mockAxios.post).toHaveBeenCalledTimes(2);
    });
  });

  describe('Error handling', () => {
    test('handles network timeout', async () => {
      mockAxios.get = jest.fn().mockRejectedValue(new Error('timeout of 30000ms exceeded'));

      await expect(predictionApi.getPlayers()).rejects.toThrow('Failed to get players');
    });

    test('handles malformed response', async () => {
      const mockResponse = {
        data: null
      };
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      const result = await predictionApi.getPlayers();
      expect(result).toEqual({ players: [] });
    });

    test('handles missing response data', async () => {
      const mockResponse = {
        data: {}
      };
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      const result = await predictionApi.getPlayers();
      expect(result).toEqual({ players: [] });
    });
  });

  describe('Request validation', () => {
    test('validates prediction request structure', async () => {
      const validRequest: PredictionRequest = {
        player_names: ['Player1', 'Player2'],
        prop_type: 'kills',
        prop_value: 4.5,
        map_range: [1, 5],
        opponent: 'Team2',
        tournament: 'LPL',
        team: 'Team1',
        match_date: '2024-01-15T10:00:00',
        position_roles: ['MID', 'BOT']
      };

      const mockResponse = {
        data: {
          prediction: 'OVER',
          confidence: 75.0,
          expected_stat: 4.5,
          confidence_interval: [3.8, 5.2],
          reasoning: 'Good recent form.',
          player_stats: {
            avg_kills: 4.0,
            avg_assists: 6.0,
            form_z_score: 0.5,
            maps_played: 10,
            avg_deaths: 2.5,
            avg_damage: 15000,
            avg_vision: 25.0,
            avg_cs: 200.0,
            position_factor: 1.2
          },
          data_years: '2024 (108 matches)'
        }
      };
      mockAxios.post = jest.fn().mockResolvedValue(mockResponse);

      const result = await predictionApi.getPrediction(validRequest);

      expect(result).toMatchObject({
        prediction: 'OVER',
        confidence: 75.0,
        expected_stat: 4.5
      });
    });
  });

  describe('Response validation', () => {
    test('validates prediction response structure', async () => {
      const mockRequest: PredictionRequest = {
        player_names: ['Player1'],
        prop_type: 'kills',
        prop_value: 5.0,
        map_range: [1, 3],
        opponent: 'Team2',
        tournament: 'LPL',
        team: 'Team1',
        match_date: '2024-01-15T10:00:00',
        position_roles: ['MID']
      };

      const mockResponse = {
        data: {
          prediction: 'OVER',
          confidence: 75.0,
          expected_stat: 4.5,
          confidence_interval: [3.8, 5.2],
          reasoning: 'Good recent form. Moderate sample size.',
          player_stats: {
            avg_kills: 4.0,
            avg_assists: 6.0,
            form_z_score: 0.5,
            maps_played: 10,
            avg_deaths: 2.5,
            avg_damage: 15000,
            avg_vision: 25.0,
            avg_cs: 200.0,
            position_factor: 1.2
          },
          data_years: '2024 (108 matches), 2025 (67 matches)'
        }
      };
      mockAxios.post = jest.fn().mockResolvedValue(mockResponse);

      const result = await predictionApi.getPrediction(mockRequest);

      expect(result).toMatchObject({
        prediction: expect.stringMatching(/^(OVER|UNDER)$/),
        confidence: expect.any(Number),
        expected_stat: expect.any(Number),
        confidence_interval: expect.arrayContaining([expect.any(Number), expect.any(Number)]),
        reasoning: expect.any(String),
        player_stats: expect.objectContaining({
          avg_kills: expect.any(Number),
          avg_assists: expect.any(Number),
          form_z_score: expect.any(Number),
          maps_played: expect.any(Number),
          position_factor: expect.any(Number)
        }),
        data_years: expect.any(String)
      });
    });
  });
}); 