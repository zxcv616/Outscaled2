import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Card,
  CardContent,
  Chip,
  Stack,
  Tooltip,
} from '@mui/material';
import {
  EmojiEvents,
  Group,
  CalendarToday,
  Info,
  AutoAwesome,
} from '@mui/icons-material';
import { EnhancedAutocomplete } from '../EnhancedAutocomplete';
import { predictionApi } from '../../../services/api';

interface MatchDetailsStepProps {
  formData: any;
  errors: Record<string, string>;
  onChange: (updates: any) => void;
}

export const MatchDetailsStep: React.FC<MatchDetailsStepProps> = ({
  formData,
  errors,
  onChange,
}) => {
  const [availableTeams, setAvailableTeams] = useState<string[]>([]);
  const [availableTournaments, setAvailableTournaments] = useState<string[]>([]);
  const [loadingTeams, setLoadingTeams] = useState(false);
  const [teamSuggestions, setTeamSuggestions] = useState<string[]>([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoadingTeams(true);
        
        const [teamsResponse, tournamentsResponse] = await Promise.all([
          predictionApi.getTeams(),
          predictionApi.getTournaments(),
        ]);
        
        setAvailableTeams(teamsResponse.teams);
        setAvailableTournaments(tournamentsResponse.tournaments);
        
        // Auto-select first tournament if none selected
        if (!formData.tournament && tournamentsResponse.tournaments.length > 0) {
          onChange({ tournament: tournamentsResponse.tournaments[0] });
        }
      } catch (error) {
        console.error('Failed to load match data:', error);
      } finally {
        setLoadingTeams(false);
      }
    };

    loadData();
  }, [formData.tournament, onChange]);

  // Generate team suggestions based on selected players
  useEffect(() => {
    const generateTeamSuggestions = () => {
      if (!formData.player_names?.length || !availableTeams.length) {
        setTeamSuggestions([]);
        return;
      }

      // Simple heuristic: suggest teams based on player names
      const suggestions = availableTeams.filter(team => {
        const teamLower = team.toLowerCase();
        return formData.player_names.some((player: string) => {
          const playerLower = player.toLowerCase();
          // Check if team name appears in player name or vice versa
          return teamLower.includes(playerLower.split(' ')[0]) || 
                 playerLower.includes(teamLower.split(' ')[0]);
        });
      }).slice(0, 3); // Limit to top 3 suggestions

      setTeamSuggestions(suggestions);
    };

    generateTeamSuggestions();
  }, [formData.player_names, availableTeams]);

  const handleDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ match_date: event.target.value });
  };

  const applySuggestedTeam = (team: string) => {
    onChange({ team });
  };

  const formatTournamentOption = (tournament: string) => {
    // Add visual indicators for different tournament types
    const tournamentLower = tournament.toLowerCase();
    let icon = '🏆';
    let category = 'Tournament';
    
    if (tournamentLower.includes('world') || tournamentLower.includes('championship')) {
      icon = '🌍';
      category = 'World Championship';
    } else if (tournamentLower.includes('spring') || tournamentLower.includes('summer')) {
      icon = '🌟';
      category = 'Regional League';
    } else if (tournamentLower.includes('msi')) {
      icon = '🎯';
      category = 'International';
    }

    return { tournament, icon, category };
  };

  const getCurrentDateTime = () => {
    const now = new Date();
    // Format for datetime-local input
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  const getDateHelperText = () => {
    if (errors.match_date) return errors.match_date;
    
    const selectedDate = new Date(formData.match_date);
    const now = new Date();
    
    if (selectedDate > now) {
      const diffHours = Math.ceil((selectedDate.getTime() - now.getTime()) / (1000 * 60 * 60));
      if (diffHours < 24) {
        return `Match is in ${diffHours} hour${diffHours !== 1 ? 's' : ''}`;
      } else {
        const diffDays = Math.ceil(diffHours / 24);
        return `Match is in ${diffDays} day${diffDays !== 1 ? 's' : ''}`;
      }
    } else {
      const diffHours = Math.ceil((now.getTime() - selectedDate.getTime()) / (1000 * 60 * 60));
      if (diffHours < 24) {
        return `Match was ${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
      } else {
        const diffDays = Math.ceil(diffHours / 24);
        return `Match was ${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
      }
    }
  };

  return (
    <Box sx={{ py: 2 }}>
      {/* Header */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
          <EmojiEvents sx={{ fontSize: 32, color: 'primary.main', mr: 1 }} />
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            Match Details
          </Typography>
        </Box>
        <Typography variant="body1" color="text.secondary">
          Specify the tournament, teams, and match timing
        </Typography>
      </Box>

      {/* Tournament Selection */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
          <EmojiEvents sx={{ mr: 1, color: 'primary.main' }} />
          Tournament
        </Typography>
        
        <FormControl fullWidth>
          <InputLabel>Tournament</InputLabel>
          <Select
            value={formData.tournament || ''}
            label="Tournament"
            onChange={(e) => onChange({ tournament: e.target.value })}
            sx={{
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: 'rgba(255, 255, 255, 0.3)',
              },
              '&:hover .MuiOutlinedInput-notchedOutline': {
                borderColor: 'primary.main',
              },
              '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                borderColor: 'primary.main',
                borderWidth: 2,
              },
            }}
          >
            {availableTournaments.map((tournament) => {
              const formatted = formatTournamentOption(tournament);
              return (
                <MenuItem key={tournament} value={tournament}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography component="span" sx={{ fontSize: '1.2rem' }}>
                      {formatted.icon}
                    </Typography>
                    <Box>
                      <Typography sx={{ fontWeight: 500 }}>
                        {formatted.tournament}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatted.category}
                      </Typography>
                    </Box>
                  </Box>
                </MenuItem>
              );
            })}
          </Select>
        </FormControl>
      </Box>

      {/* Team Selection */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
          <Group sx={{ mr: 1, color: 'primary.main' }} />
          Team (Optional)
          <Tooltip title="Leave blank to auto-infer from player history">
            <Info sx={{ ml: 1, fontSize: 16, color: 'text.secondary' }} />
          </Tooltip>
        </Typography>
        
        <EnhancedAutocomplete
          options={availableTeams}
          value={formData.team || ''}
          onChange={(value) => onChange({ team: value as string })}
          loading={loadingTeams}
          placeholder="Search teams or leave blank for auto-inference..."
          label="Team"
          helpText="Will be automatically inferred from player's recent matches if left blank"
        />

        {/* Team Suggestions */}
        {teamSuggestions.length > 0 && !formData.team && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              💡 Suggested teams based on selected players:
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {teamSuggestions.map((team) => (
                <Chip
                  key={team}
                  label={team}
                  icon={<AutoAwesome />}
                  onClick={() => applySuggestedTeam(team)}
                  sx={{
                    background: 'rgba(63, 81, 181, 0.1)',
                    border: '1px solid rgba(63, 81, 181, 0.3)',
                    color: 'primary.main',
                    cursor: 'pointer',
                    '&:hover': {
                      background: 'rgba(63, 81, 181, 0.2)',
                    },
                  }}
                />
              ))}
            </Stack>
          </Box>
        )}
      </Box>

      {/* Opponent Selection */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
          <Group sx={{ mr: 1, color: 'secondary.main' }} />
          Opponent Team
        </Typography>
        
        <EnhancedAutocomplete
          options={availableTeams}
          value={formData.opponent || ''}
          onChange={(value) => onChange({ opponent: value as string })}
          loading={loadingTeams}
          placeholder="Search opponent teams..."
          label="Opponent"
          error={errors.opponent}
          helpText="The team your selected players will be playing against"
        />
      </Box>

      {/* Match Date */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
          <CalendarToday sx={{ mr: 1, color: 'primary.main' }} />
          Match Date & Time
        </Typography>
        
        <TextField
          fullWidth
          label="Match Date & Time"
          type="datetime-local"
          value={formData.match_date || getCurrentDateTime()}
          onChange={handleDateChange}
          error={!!errors.match_date}
          helperText={getDateHelperText()}
          InputLabelProps={{ 
            shrink: true 
          }}
          sx={{
            '& .MuiOutlinedInput-root': {
              '& fieldset': {
                borderColor: 'rgba(255, 255, 255, 0.3)',
              },
              '&:hover fieldset': {
                borderColor: 'primary.main',
              },
              '&.Mui-focused fieldset': {
                borderColor: 'primary.main',
                borderWidth: 2,
              },
            },
          }}
        />
      </Box>

      {/* Form Summary */}
      {formData.tournament && formData.opponent && (
        <Card
          sx={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
          }}
        >
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
              <Info sx={{ mr: 1, color: 'info.main' }} />
              Match Summary
            </Typography>
            
            <Stack spacing={1}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  Tournament:
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {formData.tournament}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  Team:
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {formData.team || 'Auto-inferred'}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  Opponent:
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {formData.opponent}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  Match Date:
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {new Date(formData.match_date).toLocaleString()}
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      )}

      {/* Validation Alert */}
      {!formData.tournament || !formData.opponent ? (
        <Alert severity="warning" sx={{ mt: 2 }}>
          Please select both tournament and opponent to proceed to the next step.
        </Alert>
      ) : (
        <Alert severity="success" sx={{ mt: 2 }}>
          ✅ Match details are complete! You can now proceed to configure your prediction.
        </Alert>
      )}
    </Box>
  );
};