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
  { value: 'TOP', label: 'Top Lane', color: '#FF6B6B', icon: 'T' },
  { value: 'JNG', label: 'Jungle', color: '#4ECDC4', icon: 'J' },
  { value: 'MID', label: 'Mid Lane', color: '#45B7D1', icon: 'M' },
  { value: 'BOT', label: 'Bot Lane', color: '#FFA07A', icon: 'B' },
  { value: 'SUP', label: 'Support', color: '#98D8C8', icon: 'S' },
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
    
    const selectedPlayer = Array.isArray(value) ? value[0] : value;
    const newPlayers = selectedPlayer ? [selectedPlayer] : [];
    const updates: any = { player_names: newPlayers };
    
    // Auto-suggest position for single player
    if (selectedPlayer) {
      const playerLower = selectedPlayer.toLowerCase();
      let suggestedPosition = '';
      
      if (playerLower.includes('top') || playerLower.includes('impact')) {
        suggestedPosition = 'TOP';
      } else if (playerLower.includes('jungle') || playerLower.includes('jng')) {
        suggestedPosition = 'JNG';
      } else if (playerLower.includes('mid') || playerLower.includes('faker')) {
        suggestedPosition = 'MID';
      } else if (playerLower.includes('adc') || playerLower.includes('bot')) {
        suggestedPosition = 'BOT';
      } else if (playerLower.includes('sup') || playerLower.includes('support')) {
        suggestedPosition = 'SUP';
      }
      
      updates.position_roles = [suggestedPosition];
    } else {
      updates.position_roles = [];
    }
    
    onChange(updates);
  };

  const handlePositionChange = (event: SelectChangeEvent<string>) => {
    const selectedPosition = event.target.value as string;
    onChange({ position_roles: [selectedPosition] });
  };

  const applySuggestedPosition = (playerIndex: number, position: string) => {
    const newPositions = [...(formData.position_roles || [])];
    newPositions[playerIndex] = position;
    onChange({ position_roles: newPositions });
  };

  return (
    <Box sx={{ 
      py: 2,
      animation: 'fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
      '@keyframes fadeInUp': {
        '0%': {
          opacity: 0,
          transform: 'translateY(20px)',
        },
        '100%': {
          opacity: 1,
          transform: 'translateY(0px)',
        },
      },
    }}>
      {/* Header */}
      <Box sx={{ 
        mb: 4, 
        textAlign: 'center',
        animation: 'slideInDown 0.5s cubic-bezier(0.4, 0, 0.2, 1) 0.2s both',
        '@keyframes slideInDown': {
          '0%': {
            opacity: 0,
            transform: 'translateY(-20px)',
          },
          '100%': {
            opacity: 1,
            transform: 'translateY(0px)',
          },
        },
      }}>
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          mb: 2,
          transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'scale(1.05)',
          },
        }}>
          <Person sx={{ 
            fontSize: 32, 
            color: 'primary.main', 
            mr: 1,
            animation: 'iconBounce 1s ease-in-out infinite',
            '@keyframes iconBounce': {
              '0%, 20%, 50%, 80%, 100%': {
                transform: 'translateY(0)',
              },
              '40%': {
                transform: 'translateY(-4px)',
              },
              '60%': {
                transform: 'translateY(-2px)',
              },
            },
          }} />
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
        <Typography variant="h6" sx={{ 
          mb: { xs: 1.5, sm: 2 }, 
          display: 'flex', 
          alignItems: 'center',
          fontSize: { xs: '1rem', sm: '1.125rem' }
        }}>
          <Group sx={{ 
            mr: 1, 
            color: 'primary.main',
            fontSize: { xs: 20, sm: 24 }
          }} />
          Select Player
        </Typography>
        
        <EnhancedAutocomplete
          multiple={false}
          options={availablePlayers}
          value={formData.player_names?.[0] || ''}
          onChange={handlePlayerChange}
          loading={loadingPlayers}
          placeholder="Search and select a player..."
          error={errors.player_names}
          label="Player Name"
          helpText="Select one player for your prediction"
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
                    <Avatar sx={{ 
                      bgcolor: 'primary.main', 
                      fontSize: '0.75rem',
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    }}>
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
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    transform: 'scale(1)',
                    animation: 'chipSlideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                    '@keyframes chipSlideIn': {
                      '0%': {
                        opacity: 0,
                        transform: 'scale(0.8) translateX(-20px)',
                      },
                      '100%': {
                        opacity: 1,
                        transform: 'scale(1) translateX(0px)',
                      },
                    },
                    '&:hover': {
                      transform: 'scale(1.05)',
                      background: 'rgba(63, 81, 181, 0.15)',
                      boxShadow: '0 4px 12px rgba(63, 81, 181, 0.3)',
                    },
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
            Player Position
          </Typography>

          <FormControl fullWidth error={!!errors.position_roles}>
            <InputLabel>Position Role</InputLabel>
            <Select
              value={formData.position_roles?.[0] || ''}
              label="Position Role"
              onChange={handlePositionChange}
              sx={{
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                '&:hover': {
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'primary.main',
                    boxShadow: '0 0 0 1px rgba(63, 81, 181, 0.2)',
                  },
                },
                '&.Mui-focused': {
                  transform: 'scale(1.02)',
                },
              }}
            >
              {POSITIONS.map((position) => (
                <MenuItem 
                  key={position.value} 
                  value={position.value}
                  sx={{
                    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                    '&:hover': {
                      backgroundColor: 'rgba(63, 81, 181, 0.1)',
                      transform: 'translateX(4px)',
                    },
                  }}
                >
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
                Suggested Positions:
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
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                        transform: 'translateY(0px)',
                        animation: 'suggestionSlideIn 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                        '@keyframes suggestionSlideIn': {
                          '0%': {
                            opacity: 0,
                            transform: 'translateY(20px) scale(0.95)',
                          },
                          '100%': {
                            opacity: 1,
                            transform: 'translateY(0px) scale(1)',
                          },
                        },
                        '&:hover': {
                          background: 'rgba(255, 255, 255, 0.08)',
                          borderColor: 'primary.main',
                          transform: 'translateY(-2px)',
                          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.2)',
                        },
                        '&:active': {
                          transform: 'translateY(0px) scale(0.98)',
                          transition: 'all 0.1s cubic-bezier(0.4, 0, 0.2, 1)',
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
                                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                                '&:hover': {
                                  transform: 'scale(1.1)',
                                  boxShadow: `0 0 10px ${positionInfo?.color || 'grey'}`,
                                },
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

    </Box>
  );
};