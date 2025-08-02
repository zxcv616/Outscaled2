import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Alert,
  Card,
  CardContent,
  Avatar,
  Stack,
  Tooltip,
} from '@mui/material';
import {
  Person,
  SportsEsports,
  StarBorder,
  Group,
} from '@mui/icons-material';
import { EnhancedAutocomplete } from '../EnhancedAutocomplete';
import { predictionApi } from '../../../services/api';

interface PlayerSelectionStepProps {
  formData: any;
  errors: Record<string, string>;
  onChange: (updates: any) => void;
}

const POSITIONS = [
  { value: 'TOP', label: 'Top Lane', color: '#FF6B6B', icon: '⚔️' },
  { value: 'JNG', label: 'Jungle', color: '#4ECDC4', icon: '🌲' },
  { value: 'MID', label: 'Mid Lane', color: '#45B7D1', icon: '⚡' },
  { value: 'BOT', label: 'Bot Lane', color: '#FFA07A', icon: '🏹' },
  { value: 'SUP', label: 'Support', color: '#98D8C8', icon: '🛡️' },
];

export const PlayerSelectionStep: React.FC<PlayerSelectionStepProps> = ({
  formData,
  errors,
  onChange,
}) => {
  const [availablePlayers, setAvailablePlayers] = useState<string[]>([]);
  const [loadingPlayers, setLoadingPlayers] = useState(false);
  const [playerSuggestions, setPlayerSuggestions] = useState<Record<string, string>>({});

  useEffect(() => {
    const loadPlayers = async () => {
      try {
        setLoadingPlayers(true);
        const response = await predictionApi.getPlayers();
        setAvailablePlayers(response.players);
      } catch (error) {
        console.error('Failed to load players:', error);
      } finally {
        setLoadingPlayers(false);
      }
    };

    loadPlayers();
  }, []);

  // Auto-suggest positions based on common player-position combinations
  useEffect(() => {
    const updateSuggestions = () => {
      const suggestions: Record<string, string> = {};
      formData.player_names?.forEach((player: string, index: number) => {
        // Simple heuristics for position suggestions
        const playerLower = player.toLowerCase();
        if (playerLower.includes('top') || playerLower.includes('impact')) {
          suggestions[player] = 'TOP';
        } else if (playerLower.includes('jungle') || playerLower.includes('jng')) {
          suggestions[player] = 'JNG';
        } else if (playerLower.includes('mid') || playerLower.includes('faker')) {
          suggestions[player] = 'MID';
        } else if (playerLower.includes('adc') || playerLower.includes('bot')) {
          suggestions[player] = 'BOT';
        } else if (playerLower.includes('sup') || playerLower.includes('support')) {
          suggestions[player] = 'SUP';
        }
      });
      setPlayerSuggestions(suggestions);
    };

    updateSuggestions();
  }, [formData.player_names]);

  const handlePlayerChange = (value: string | string[]) => {
    const newPlayers = Array.isArray(value) ? value : [value].filter(Boolean);
    const updates: any = { player_names: newPlayers };
    
    // Auto-adjust position_roles array to match player count
    if (newPlayers.length !== formData.position_roles?.length) {
      const newPositions = [...(formData.position_roles || [])];
      
      if (newPlayers.length > newPositions.length) {
        // Add suggested positions for new players
        for (let i = newPositions.length; i < newPlayers.length; i++) {
          const player = newPlayers[i];
          const suggestedPosition = playerSuggestions[player] || '';
          newPositions.push(suggestedPosition);
        }
      } else {
        // Remove excess positions
        newPositions.splice(newPlayers.length);
      }
      
      updates.position_roles = newPositions;
    }
    
    onChange(updates);
  };

  const handlePositionChange = (event: SelectChangeEvent<string[]>) => {
    const positions = typeof event.target.value === 'string' 
      ? event.target.value.split(',') 
      : event.target.value;
    
    onChange({ position_roles: positions });
  };

  const applySuggestedPosition = (playerIndex: number, position: string) => {
    const newPositions = [...(formData.position_roles || [])];
    newPositions[playerIndex] = position;
    onChange({ position_roles: newPositions });
  };

  return (
    <Box sx={{ py: 2 }}>
      {/* Header */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
          <Person sx={{ fontSize: 32, color: 'primary.main', mr: 1 }} />
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            Select Players & Positions
          </Typography>
        </Box>
        <Typography variant="body1" color="text.secondary">
          Choose the players you want to predict and their positions
        </Typography>
      </Box>

      {/* Player Selection */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
          <Group sx={{ mr: 1, color: 'primary.main' }} />
          Players
        </Typography>
        
        <EnhancedAutocomplete
          multiple
          options={availablePlayers}
          value={formData.player_names || []}
          onChange={handlePlayerChange}
          loading={loadingPlayers}
          placeholder="Search and select players..."
          error={errors.player_names}
          label="Player Names"
          helpText="Select 1-5 players for your prediction"
        />

        {formData.player_names?.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Selected Players:
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {formData.player_names.map((player: string, index: number) => (
                <Chip
                  key={`${player}-${index}`}
                  avatar={
                    <Avatar sx={{ bgcolor: 'primary.main', fontSize: '0.75rem' }}>
                      {player.charAt(0).toUpperCase()}
                    </Avatar>
                  }
                  label={player}
                  color="primary"
                  variant="outlined"
                  sx={{
                    background: 'rgba(63, 81, 181, 0.1)',
                    borderColor: 'primary.main',
                    mb: 1,
                  }}
                />
              ))}
            </Stack>
          </Box>
        )}
      </Box>

      {/* Position Selection */}
      {formData.player_names?.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
            <SportsEsports sx={{ mr: 1, color: 'secondary.main' }} />
            Positions
          </Typography>

          <FormControl fullWidth error={!!errors.position_roles}>
            <InputLabel>Position Roles</InputLabel>
            <Select
              multiple
              value={formData.position_roles || []}
              label="Position Roles"
              onChange={handlePositionChange}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {(selected as string[]).map((value, index) => {
                    const position = POSITIONS.find(p => p.value === value);
                    return (
                      <Chip
                        key={`${value}-${index}`}
                        label={position?.label || value}
                        size="small"
                        sx={{
                          backgroundColor: position?.color || 'grey.500',
                          color: 'white',
                          fontWeight: 500,
                        }}
                      />
                    );
                  })}
                </Box>
              )}
            >
              {POSITIONS.map((position) => (
                <MenuItem key={position.value} value={position.value}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography component="span" sx={{ fontSize: '1.2rem' }}>
                      {position.icon}
                    </Typography>
                    <Typography sx={{ fontWeight: 500 }}>
                      {position.label}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {errors.position_roles && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {errors.position_roles}
            </Alert>
          )}

          {/* Position Suggestions */}
          {Object.keys(playerSuggestions).length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                💡 Position Suggestions:
              </Typography>
              <Stack spacing={1}>
                {formData.player_names?.map((player: string, index: number) => {
                  const suggestedPosition = playerSuggestions[player];
                  const currentPosition = formData.position_roles?.[index];
                  
                  if (!suggestedPosition || currentPosition === suggestedPosition) {
                    return null;
                  }

                  const positionInfo = POSITIONS.find(p => p.value === suggestedPosition);
                  
                  return (
                    <Card
                      key={`suggestion-${player}`}
                      sx={{
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        '&:hover': {
                          background: 'rgba(255, 255, 255, 0.08)',
                          borderColor: 'primary.main',
                        },
                      }}
                      onClick={() => applySuggestedPosition(index, suggestedPosition)}
                    >
                      <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              {player}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              →
                            </Typography>
                            <Chip
                              label={positionInfo?.label || suggestedPosition}
                              size="small"
                              sx={{
                                backgroundColor: positionInfo?.color || 'grey.500',
                                color: 'white',
                                fontWeight: 500,
                              }}
                            />
                          </Box>
                          <Tooltip title="Click to apply suggestion">
                            <StarBorder sx={{ fontSize: 16, color: 'text.secondary' }} />
                          </Tooltip>
                        </Box>
                      </CardContent>
                    </Card>
                  );
                })}
              </Stack>
            </Box>
          )}
        </Box>
      )}

      {/* Validation Summary */}
      {formData.player_names?.length > 0 && formData.position_roles?.length > 0 && (
        <Alert
          severity={
            formData.player_names.length === formData.position_roles.length ? 'success' : 'warning'
          }
          sx={{ mt: 2 }}
        >
          {formData.player_names.length === formData.position_roles.length
            ? `✅ Perfect! You have selected ${formData.player_names.length} players with matching positions.`
            : `⚠️ Please ensure you have ${formData.player_names.length} positions for your ${formData.player_names.length} players.`}
        </Alert>
      )}
    </Box>
  );
};