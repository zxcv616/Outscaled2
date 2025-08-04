import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Chip,
  Autocomplete,
  Alert,
  Divider,
  CircularProgress,
} from '@mui/material';

import { 
  Person, 
  TrendingUp, 
  SportsEsports, 
  Group,
  EmojiEvents,
} from '@mui/icons-material';
import { PredictionRequest } from '../types/api';
import { predictionApi } from '../services/api';
import { usePlayerSearch } from '../hooks/usePlayerSearch';

interface PredictionFormProps {
  onSubmit: (request: PredictionRequest) => void;
  loading: boolean;
}

const POSITIONS = ['TOP', 'JNG', 'MID', 'BOT', 'SUP'];
const PROP_TYPES = ['kills', 'assists'];

export const PredictionForm: React.FC<PredictionFormProps> = ({ onSubmit, loading }) => {
  const [formData, setFormData] = useState<Partial<PredictionRequest>>({
    player_names: [],
    prop_type: 'kills',
    prop_value: 0,
    map_range: [1, 2],
    opponent: '',
    tournament: '',
    team: '',
    position_roles: [],
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [availableTeams, setAvailableTeams] = useState<string[]>([]);
  const [availableTournaments, setAvailableTournaments] = useState<string[]>([]);
  const [availableOpponents, setAvailableOpponents] = useState<string[]>([]);
  const [playerDetails, setPlayerDetails] = useState<Record<string, { position: string | null; team: string | null; games_played: number }>>({});
  const [loadingData, setLoadingData] = useState(true);

  // Use optimized player search instead of loading all players
  const { searchQuery, setSearchQuery, searchResults: availablePlayers, loading: searchLoading, totalMatches } = usePlayerSearch();

  // Load available teams, tournaments, opponents, and player details on component mount
  // Note: Players are loaded via usePlayerSearch hook for better performance
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoadingData(true);
        
        // Check if backend is ready first
        const healthResponse = await predictionApi.getHealth();
        if (!healthResponse || healthResponse.status !== 'healthy') {
          console.log('Backend not ready, will retry...');
          setTimeout(loadData, 2000); // Retry after 2 seconds
          return;
        }
        
        const [teamsResponse, tournamentsResponse, opponentsResponse, playerDetailsResponse] = await Promise.all([
          predictionApi.getTeams(),
          predictionApi.getTournaments(),
          predictionApi.getOpponents(),
          predictionApi.getPlayerDetails()
        ]);
        
        setAvailableTeams(teamsResponse.teams || []);
        setAvailableTournaments(tournamentsResponse.tournaments || []);
        setAvailableOpponents(opponentsResponse.opponents || []);
        
        // Use real player details from CSV data
        setPlayerDetails(playerDetailsResponse.player_details || {});
        
        // Set default tournament to first available one if none selected
        if (!formData.tournament && tournamentsResponse.tournaments && tournamentsResponse.tournaments.length > 0) {
          setFormData(prev => ({ ...prev, tournament: tournamentsResponse.tournaments[0] }));
        }
      } catch (error) {
        console.error('Failed to load autocomplete data:', error);
        // Retry after error
        setTimeout(loadData, 3000);
      } finally {
        setLoadingData(false);
      }
    };

    loadData();
  }, []);

  // Auto-assign position and team when players are selected
  useEffect(() => {
    if (formData.player_names?.length) {
      // Use real player details from CSV data
      const positions = new Set<string>();
      const teams = new Set<string>();
      
      formData.player_names.forEach(playerName => {
        const playerInfo = playerDetails && playerDetails[playerName];
        if (playerInfo) {
          if (playerInfo.position) positions.add(playerInfo.position);
          if (playerInfo.team) teams.add(playerInfo.team);
        }
      });
      
      // Auto-set position if not already set (convert to uppercase)
      if (positions.size > 0 && !formData.position_roles?.length) {
        const upperPositions = Array.from(positions).map(p => p.toUpperCase());
        setFormData(prev => ({ ...prev, position_roles: upperPositions }));
      }
      
      // Auto-set team if not already set and all players from same team
      if (teams.size === 1 && !formData.team) {
        setFormData(prev => ({ ...prev, team: Array.from(teams)[0] }));
      }
    }
  }, [formData.player_names, playerDetails]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.player_names?.length) {
      newErrors.player_names = 'At least one player is required';
    }

    if (!formData.prop_value || formData.prop_value <= 0) {
      newErrors.prop_value = 'Prop value must be greater than 0';
    }

    if (!formData.opponent) {
      newErrors.opponent = 'Opponent is required';
    }

    if (!formData.team) {
      newErrors.team = 'Team is required';
    }

    if (!formData.position_roles?.length) {
      newErrors.position_roles = 'At least one position is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm() && formData.player_names && formData.position_roles) {
      onSubmit({
        player_names: formData.player_names,
        prop_type: formData.prop_type as 'kills' | 'assists',
        prop_value: formData.prop_value!,
        map_range: formData.map_range as [number, number],
        opponent: formData.opponent!,
        tournament: formData.tournament!,
        team: formData.team!,
        position_roles: formData.position_roles,
      });
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography 
          variant="h4" 
          gutterBottom 
          sx={{ 
            fontWeight: 700,
            background: 'linear-gradient(45deg, #3f51b5, #f50057)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mb: 1,
          }}
        >
          Create Your Prediction
        </Typography>
        <Typography 
          variant="body1" 
          color="text.secondary"
          sx={{ maxWidth: 600, mx: 'auto' }}
        >
          Fill in the details below to get an AI-powered prediction for your League of Legends prop bet
        </Typography>
      </Box>
      
      <Box component="form" onSubmit={handleSubmit}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Player Names */}
          <Box sx={{ width: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Person sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Players
              </Typography>
            </Box>
            <Autocomplete
              multiple
              freeSolo
              options={availablePlayers}
              value={formData.player_names || []}
              onChange={(_, newValue) => 
                setFormData(prev => ({ ...prev, player_names: newValue }))
              }
              loading={searchLoading}
              onInputChange={(_, value) => {
                setSearchQuery(value);
              }}
              filterOptions={(options) => options} // No client-side filtering, server handles it
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Player Names"
                  error={!!errors.player_names}
                  helperText={
                    errors.player_names || 
                    (searchLoading ? 'Searching players...' : 
                     totalMatches > 0 ? `${totalMatches} matches found` : 
                     searchQuery.length >= 2 ? 'No matches found' :
                     'Type at least 2 characters to search players')
                  }
                  placeholder="Type to search players... (e.g., 'faker')"
                  fullWidth
                  InputProps={{
                    ...params.InputProps,
                    endAdornment: (
                      <>
                        {searchLoading && <CircularProgress size={20} />}
                        {params.InputProps.endAdornment}
                      </>
                    ),
                  }}
                />
              )}
              renderOption={(props, option) => {
                const details = playerDetails[option];
                const { key, ...otherProps } = props;
                return (
                  <Box component="li" key={key} {...otherProps}>
                    <Box>
                      <Typography variant="body1">{option}</Typography>
                      {details && (
                        <Typography variant="caption" color="text.secondary">
                          {details.position ? `${details.position} • ` : ''}
                          {details.team ? `${details.team} • ` : ''}
                          {details.games_played} games
                        </Typography>
                      )}
                    </Box>
                  </Box>
                );
              }}
              renderTags={(value, getTagProps) =>
                value.map((option, index) => {
                  const details = playerDetails[option];
                  const { key, ...chipProps } = getTagProps({ index });
                  return (
                    <Chip
                      key={key}
                      variant="outlined"
                      label={`${option}${details?.position ? ` (${details.position})` : ''}`}
                      {...chipProps}
                      sx={{ 
                        background: 'rgba(63, 81, 181, 0.1)',
                        borderColor: 'primary.main',
                        color: 'primary.main',
                      }}
                    />
                  );
                })
              }
            />
          </Box>

          {/* Prop Type and Value */}
          <Box sx={{ width: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <TrendingUp sx={{ mr: 1, color: 'secondary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Prop Details
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <FormControl sx={{ flex: 1 }}>
                <InputLabel>Prop Type</InputLabel>
                <Select
                  value={formData.prop_type}
                  label="Prop Type"
                  onChange={(e) => 
                    setFormData(prev => ({ ...prev, prop_type: e.target.value as 'kills' | 'assists' }))
                  }
                >
                  {PROP_TYPES.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <TextField
                sx={{ flex: 1 }}
                label="Prop Value"
                type="number"
                value={formData.prop_value}
                onChange={(e) => 
                  setFormData(prev => ({ ...prev, prop_value: parseFloat(e.target.value) || 0 }))
                }
                error={!!errors.prop_value}
                helperText={errors.prop_value}
                inputProps={{ step: 0.5, min: 0 }}
              />
            </Box>
          </Box>

          {/* Map Range */}
          <Box sx={{ width: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <SportsEsports sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Map Range
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <TextField
                label="Start"
                type="number"
                value={formData.map_range?.[0] || 1}
                onChange={(e) => {
                  const start = parseInt(e.target.value) || 1;
                  setFormData(prev => ({
                    ...prev,
                    map_range: [start, prev.map_range?.[1] || 2]
                  }));
                }}
                inputProps={{ min: 1, max: 5 }}
                sx={{ flex: 1 }}
              />
              <Typography sx={{ fontWeight: 600, color: 'text.secondary' }}>to</Typography>
              <TextField
                label="End"
                type="number"
                value={formData.map_range?.[1] || 2}
                onChange={(e) => {
                  const end = parseInt(e.target.value) || 2;
                  setFormData(prev => ({
                    ...prev,
                    map_range: [prev.map_range?.[0] || 1, end]
                  }));
                }}
                inputProps={{ min: 1, max: 5 }}
                sx={{ flex: 1 }}
              />
            </Box>
          </Box>


          {/* Team and Opponent */}
          <Box sx={{ width: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Group sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Team
              </Typography>
            </Box>
            <Autocomplete
              options={availableTeams}
              value={formData.team}
              onChange={(_, newValue) => 
                setFormData(prev => ({ ...prev, team: newValue || '' }))
              }
              loading={loadingData}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Team"
                  error={!!errors.team}
                  helperText={errors.team}
                  placeholder="Type to search teams..."
                  fullWidth
                  InputProps={{
                    ...params.InputProps,
                    endAdornment: (
                      <>
                        {loadingData ? <Typography variant="caption">Loading...</Typography> : null}
                        {params.InputProps.endAdornment}
                      </>
                    ),
                  }}
                />
              )}
            />
          </Box>

          <Box sx={{ width: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Group sx={{ mr: 1, color: 'secondary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Opponent
              </Typography>
            </Box>
            <Autocomplete
              options={availableOpponents}
              value={formData.opponent}
              onChange={(_, newValue) => 
                setFormData(prev => ({ ...prev, opponent: newValue || '' }))
              }
              loading={loadingData}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Opponent"
                  error={!!errors.opponent}
                  helperText={errors.opponent || "Select opponent team"}
                  placeholder="Type to search opponents..."
                  fullWidth
                  InputProps={{
                    ...params.InputProps,
                    endAdornment: (
                      <>
                        {loadingData ? <Typography variant="caption">Loading...</Typography> : null}
                        {params.InputProps.endAdornment}
                      </>
                    ),
                  }}
                />
              )}
            />
          </Box>

          {/* Tournament */}
          <Box sx={{ width: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <EmojiEvents sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Tournament
              </Typography>
            </Box>
            <FormControl fullWidth>
              <InputLabel>Tournament</InputLabel>
              <Select
                value={formData.tournament}
                label="Tournament"
                onChange={(e) => 
                  setFormData(prev => ({ ...prev, tournament: e.target.value }))
                }
              >
                {availableTournaments.map((tournament) => (
                  <MenuItem key={tournament} value={tournament}>
                    {tournament}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {/* Position Roles */}
          <Box sx={{ width: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Person sx={{ mr: 1, color: 'secondary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Positions
              </Typography>
            </Box>
            <FormControl fullWidth>
              <InputLabel>Position Roles</InputLabel>
              <Select
                multiple
                value={formData.position_roles || []}
                label="Position Roles"
                onChange={(e) => 
                  setFormData(prev => ({ 
                    ...prev, 
                    position_roles: typeof e.target.value === 'string' 
                      ? e.target.value.split(',') 
                      : e.target.value 
                  }))
                }
                error={!!errors.position_roles}
              >
                {POSITIONS.map((position) => (
                  <MenuItem key={position} value={position}>
                    {position}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {errors.position_roles && (
              <Alert severity="error" sx={{ mt: 1 }}>
                {errors.position_roles}
              </Alert>
            )}
          </Box>

          {/* Submit Button */}
          <Box sx={{ width: '100%' }}>
            <Divider sx={{ my: 3 }} />
            <Button
              type="submit"
              variant="contained"
              size="large"
              fullWidth
              disabled={loading}
              sx={{ 
                py: 2,
                fontSize: '1.1rem',
                fontWeight: 600,
                background: 'linear-gradient(45deg, #3f51b5, #f50057)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #303f9f, #c51162)',
                },
                boxShadow: '0 8px 32px rgba(63, 81, 181, 0.3)',
              }}
            >
              {loading ? 'Getting Prediction...' : 'Get AI Prediction'}
            </Button>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}; 