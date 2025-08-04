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
import { 
  usePlayerSearch,
  useTeams,
  useTournaments,
  useOpponents,
  usePlayerDetails,
  useHealthCheck
} from '../hooks/useApiQueries';
import { useDebounce } from '../hooks/useDebounce';

interface OptimizedPredictionFormProps {
  onSubmit: (request: PredictionRequest) => void;
  loading: boolean;
}

const POSITIONS = ['TOP', 'JNG', 'MID', 'BOT', 'SUP'];
const PROP_TYPES = ['kills', 'assists'];

export const OptimizedPredictionForm: React.FC<OptimizedPredictionFormProps> = ({ onSubmit, loading }) => {
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
  const [playerSearchQuery, setPlayerSearchQuery] = useState('');
  
  // Debounce the search query to avoid too many API calls
  const debouncedPlayerSearch = useDebounce(playerSearchQuery, 300);

  // TanStack Query hooks
  const { data: healthData } = useHealthCheck();
  const { data: playerSearchData, isLoading: isSearchingPlayers } = usePlayerSearch(debouncedPlayerSearch);
  const { data: teamsData, isLoading: isLoadingTeams, error: teamsError } = useTeams();
  const { data: tournamentsData, isLoading: isLoadingTournaments, error: tournamentsError } = useTournaments();
  const { data: opponentsData, isLoading: isLoadingOpponents, error: opponentsError } = useOpponents();
  const { data: playerDetailsData, isLoading: isLoadingPlayerDetails, error: playerDetailsError } = usePlayerDetails();

  // Extract data with fallbacks
  const availablePlayers = playerSearchData?.players || [];
  const totalMatches = playerSearchData?.total_matches || 0;
  const availableTeams = teamsData?.teams || [];
  const availableTournaments = tournamentsData?.tournaments || [];
  const availableOpponents = opponentsData?.opponents || [];
  const playerDetails = playerDetailsData?.player_details || {};

  // Set default tournament when data loads
  useEffect(() => {
    if (!formData.tournament && availableTournaments.length > 0) {
      setFormData(prev => ({ ...prev, tournament: availableTournaments[0] }));
    }
  }, [availableTournaments, formData.tournament]);

  // Auto-assign position and team when players are selected
  useEffect(() => {
    if (formData.player_names?.length && Object.keys(playerDetails).length > 0) {
      const positions = new Set<string>();
      const teams = new Set<string>();
      
      formData.player_names.forEach(playerName => {
        const details = playerDetails[playerName];
        if (details) {
          if (details.position) positions.add(details.position);
          if (details.team) teams.add(details.team);
        }
      });

      const uniquePositions = Array.from(positions);
      const uniqueTeams = Array.from(teams);

      if (uniquePositions.length === 1 && !formData.position_roles?.length) {
        setFormData(prev => ({ ...prev, position_roles: uniquePositions }));
      }

      if (uniqueTeams.length === 1 && !formData.team) {
        setFormData(prev => ({ ...prev, team: uniqueTeams[0] }));
      }
    }
  }, [formData.player_names, playerDetails, formData.position_roles, formData.team]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.player_names?.length) {
      newErrors.player_names = 'At least one player is required';
    }

    if (!formData.prop_type) {
      newErrors.prop_type = 'Prop type is required';
    }

    if (!formData.prop_value || formData.prop_value <= 0) {
      newErrors.prop_value = 'Prop value must be greater than 0';
    }

    if (!formData.map_range || formData.map_range.length !== 2) {
      newErrors.map_range = 'Map range is required';
    }

    if (!formData.opponent) {
      newErrors.opponent = 'Opponent is required';
    }

    if (!formData.tournament) {
      newErrors.tournament = 'Tournament is required';
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
    if (validateForm()) {
      onSubmit(formData as PredictionRequest);
    }
  };

  // Show loading state for critical data
  const isCriticalDataLoading = isLoadingTeams || isLoadingTournaments || isLoadingOpponents;

  // Show API errors
  const apiErrors = [teamsError, tournamentsError, opponentsError, playerDetailsError]
    .filter(Boolean)
    .map(error => error?.message || 'Unknown error');

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
      {/* API Health Status */}
      <Box sx={{ mb: 2 }}>
        {healthData?.status === 'healthy' ? (
          <Alert severity="success" sx={{ mb: 2 }}>
            ✅ API Connected - Real LoL data loaded
          </Alert>
        ) : (
          <Alert severity="warning" sx={{ mb: 2 }}>
            ⚠️ API Status Unknown
          </Alert>
        )}
      </Box>

      {/* API Errors */}
      {apiErrors.length > 0 && (
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="body2">
            <strong>API Errors:</strong>
          </Typography>
          {apiErrors.map((error, index) => (
            <Typography key={index} variant="body2">
              • {error}
            </Typography>
          ))}
        </Alert>
      )}

      {/* Loading State */}
      {isCriticalDataLoading && (
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <CircularProgress size={20} sx={{ mr: 1 }} />
          <Typography variant="body2">Loading data...</Typography>
        </Box>
      )}

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Players Section */}
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <Person color="primary" />
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
            onInputChange={(_, value) => {
              setPlayerSearchQuery(value);
            }}
            loading={isSearchingPlayers}
            filterOptions={(options) => options} // Server-side filtering
            renderInput={(params) => (
              <TextField
                {...params}
                label="Player Names"
                error={!!errors.player_names}
                helperText={
                  errors.player_names || 
                  `Type at least 2 characters to search ${totalMatches > 0 ? `(${totalMatches} matches)` : 'players'}`
                }
                placeholder="Type to search players... (e.g., 'faker')"
                fullWidth
                InputProps={{
                  ...params.InputProps,
                  endAdornment: (
                    <>
                      {isSearchingPlayers && <CircularProgress size={20} />}
                      {params.InputProps.endAdornment}
                    </>
                  ),
                }}
              />
            )}
            renderOption={(props, option) => {
              const details = playerDetails[option];
              return (
                <Box component="li" {...props}>
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
                const { key, ...tagProps } = getTagProps({ index });
                return (
                  <Chip
                    key={key}
                    variant="outlined"
                    label={`${option}${details?.position ? ` (${details.position})` : ''}`}
                    {...tagProps}
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

        <Divider />

        {/* Prop Settings Section */}
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <TrendingUp color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Prop Settings
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <FormControl sx={{ minWidth: 120 }}>
              <InputLabel>Prop Type</InputLabel>
              <Select
                value={formData.prop_type || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, prop_type: e.target.value as 'kills' | 'assists' }))}
                label="Prop Type"
                error={!!errors.prop_type}
              >
                {PROP_TYPES.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              label="Prop Value"
              type="number"
              value={formData.prop_value || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, prop_value: parseFloat(e.target.value) || 0 }))}
              error={!!errors.prop_value}
              helperText={errors.prop_value}
              inputProps={{ min: 0, step: 0.5 }}
              sx={{ minWidth: 120 }}
            />

            <TextField
              label="Map Start"
              type="number"
              value={formData.map_range?.[0] || 1}
              onChange={(e) => {
                const newStart = parseInt(e.target.value) || 1;
                const currentEnd = formData.map_range?.[1] || 2;
                setFormData(prev => ({ ...prev, map_range: [newStart, Math.max(newStart, currentEnd)] }));
              }}
              inputProps={{ min: 1, max: 5 }}
              sx={{ minWidth: 100 }}
            />

            <TextField
              label="Map End"
              type="number"
              value={formData.map_range?.[1] || 2}
              onChange={(e) => {
                const newEnd = parseInt(e.target.value) || 2;
                const currentStart = formData.map_range?.[0] || 1;
                setFormData(prev => ({ ...prev, map_range: [Math.min(currentStart, newEnd), newEnd] }));
              }}
              inputProps={{ min: 1, max: 5 }}
              sx={{ minWidth: 100 }}
            />
          </Box>
        </Box>

        <Divider />

        {/* Match Context Section */}
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <SportsEsports color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Match Context
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Autocomplete
              options={availableOpponents}
              value={formData.opponent || ''}
              onChange={(_, newValue) => setFormData(prev => ({ ...prev, opponent: newValue || '' }))}
              loading={isLoadingOpponents}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Opponent Team"
                  error={!!errors.opponent}
                  helperText={errors.opponent}
                  sx={{ minWidth: 200 }}
                  InputProps={{
                    ...params.InputProps,
                    endAdornment: (
                      <>
                        {isLoadingOpponents && <CircularProgress size={20} />}
                        {params.InputProps.endAdornment}
                      </>
                    ),
                  }}
                />
              )}
            />

            <Autocomplete
              options={availableTournaments}
              value={formData.tournament || ''}
              onChange={(_, newValue) => setFormData(prev => ({ ...prev, tournament: newValue || '' }))}
              loading={isLoadingTournaments}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Tournament"
                  error={!!errors.tournament}
                  helperText={errors.tournament}
                  sx={{ minWidth: 200 }}
                  InputProps={{
                    ...params.InputProps,
                    endAdornment: (
                      <>
                        {isLoadingTournaments && <CircularProgress size={20} />}
                        {params.InputProps.endAdornment}
                      </>
                    ),
                  }}
                />
              )}
            />
          </Box>
        </Box>

        <Divider />

        {/* Team & Position Section */}
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <Group color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Team & Position
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Autocomplete
              options={availableTeams}
              value={formData.team || ''}
              onChange={(_, newValue) => setFormData(prev => ({ ...prev, team: newValue || '' }))}
              loading={isLoadingTeams}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Team"
                  error={!!errors.team}
                  helperText={errors.team}
                  sx={{ minWidth: 200 }}
                  InputProps={{
                    ...params.InputProps,
                    endAdornment: (
                      <>
                        {isLoadingTeams && <CircularProgress size={20} />}
                        {params.InputProps.endAdornment}
                      </>
                    ),
                  }}
                />
              )}
            />

            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Positions</InputLabel>
              <Select
                multiple
                value={formData.position_roles || []}
                onChange={(e) => {
                  const value = typeof e.target.value === 'string' ? e.target.value.split(',') : e.target.value;
                  setFormData(prev => ({ ...prev, position_roles: value }));
                }}
                label="Positions"
                error={!!errors.position_roles}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {POSITIONS.map((position) => (
                  <MenuItem key={position} value={position}>
                    {position}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Box>

        {/* Submit Button */}
        <Box sx={{ display: 'flex', justifyContent: 'center', pt: 2 }}>
          <Button
            type="submit"
            variant="contained"
            size="large"
            disabled={loading || isCriticalDataLoading}
            startIcon={loading ? <CircularProgress size={20} /> : <EmojiEvents />}
            sx={{
              minWidth: 200,
              py: 1.5,
              fontSize: '1.1rem',
              fontWeight: 600,
              background: 'linear-gradient(45deg, #3f51b5, #f50057)',
              '&:hover': {
                background: 'linear-gradient(45deg, #303f9f, #c51162)',
              },
            }}
          >
            {loading ? 'Analyzing...' : 'Get Prediction'}
          </Button>
        </Box>
      </Box>
    </Box>
  );
};