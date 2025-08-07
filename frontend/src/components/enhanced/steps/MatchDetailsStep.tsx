import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
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
  const [loadingTournaments, setLoadingTournaments] = useState(false);
  const [teamSuggestions, setTeamSuggestions] = useState<string[]>([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoadingTeams(true);
        setLoadingTournaments(true);
        
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
        setLoadingTournaments(false);
      }
    };

    loadData();
  }, [formData.tournament, onChange]);

  // Generate team suggestions based on selected players
  useEffect(() => {
    const generateTeamSuggestions = async () => {
      if (!formData.player_names?.length || !availableTeams.length) {
        setTeamSuggestions([]);
        return;
      }

      // Better team matching logic
      const suggestions: string[] = [];
      
      // Known team mappings for common players (this would ideally come from the API)
      const playerTeamMappings: Record<string, string[]> = {
        // Professional players and their known teams
        'faker': ['T1', 'SK Telecom T1'],
        'caps': ['G2 Esports'],
        'bjergsen': ['Team SoloMid', 'TSM'],
        'doublelift': ['Team Liquid', 'TSM'],
        'impact': ['Team Liquid'],
        'jensen': ['Team Liquid', 'Cloud9'],
        'perkz': ['G2 Esports', 'Cloud9'],
        'rekkles': ['Fnatic', 'G2 Esports'],
        'uzi': ['Royal Never Give Up', 'RNG'],
        'deft': ['DRX', 'KT Rolster'],
        'showmaker': ['DAMWON KIA'],
        'canyon': ['DAMWON KIA'],
        'chovy': ['Gen.G', 'Griffin'],
        'ruler': ['Gen.G', 'Samsung Galaxy'],
        'knight': ['Top Esports'],
        'jackeylove': ['Top Esports', 'Invictus Gaming'],
        'theshy': ['Invictus Gaming'],
        'rookie': ['Invictus Gaming'],
        'ning': ['Invictus Gaming'],
      };

      // Check each selected player
      for (const player of formData.player_names) {
        const playerLower = player.toLowerCase();
        
        // First, check our known mappings
        const knownTeams = playerTeamMappings[playerLower];
        if (knownTeams) {
          for (const knownTeam of knownTeams) {
            const matchingTeam = availableTeams.find(team => 
              team.toLowerCase().includes(knownTeam.toLowerCase()) ||
              knownTeam.toLowerCase().includes(team.toLowerCase())
            );
            if (matchingTeam && !suggestions.includes(matchingTeam)) {
              suggestions.push(matchingTeam);
            }
          }
        }
        
        // Fallback: Look for exact or partial matches in team names
        // But be more strict to avoid false positives
        if (suggestions.length < 3) {
          const exactMatches = availableTeams.filter(team => {
            const teamLower = team.toLowerCase();
            const teamWords = teamLower.split(/\s+/);
            const playerWords = playerLower.split(/\s+/);
            
            // Check if any significant word from player name matches team name
            return playerWords.some((playerWord: string) => 
              playerWord.length > 2 && // Ignore short words
              teamWords.some((teamWord: string) => 
                teamWord.length > 2 &&
                (teamWord.includes(playerWord) || playerWord.includes(teamWord))
              )
            );
          });
          
          // Only add if the match seems reasonable (avoid generic matches)
          for (const match of exactMatches) {
            if (!suggestions.includes(match) && 
                !match.toLowerCase().includes('one man') && // Avoid "A One Man's Army"
                !match.toLowerCase().includes('army') &&
                match.length > 3) { // Avoid very short team names
              suggestions.push(match);
            }
          }
        }
      }

      setTeamSuggestions(suggestions.slice(0, 3));
    };

    generateTeamSuggestions();
  }, [formData.player_names, availableTeams]);

  const handleDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ match_date: event.target.value });
  };

  const applySuggestedTeam = (team: string) => {
    onChange({ team });
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
    <Box>

      {/* Tournament Selection */}
      <Box sx={{ mb: 1.5 }}>
        <Typography variant="body2" sx={{ 
          mb: 1, 
          display: 'flex', 
          alignItems: 'center',
          fontWeight: 500
        }}>
          <EmojiEvents sx={{ mr: 0.5, color: 'primary.main', fontSize: 16 }} />
          Tournament
        </Typography>
        
        <EnhancedAutocomplete
          options={availableTournaments}
          value={formData.tournament || ''}
          onChange={(value) => onChange({ tournament: value as string })}
          loading={loadingTournaments}
          placeholder="Search tournaments..."
          label="Tournament"
          error={errors.tournament}
          helpText="Select the tournament where this match is taking place"
        />
      </Box>

      {/* Team Selection */}
      <Box sx={{ mb: 1.5 }}>
        <Typography variant="body2" sx={{ mb: 1, display: 'flex', alignItems: 'center', fontWeight: 500 }}>
          <Group sx={{ mr: 0.5, color: 'primary.main', fontSize: 16 }} />
          Team (Optional)
          <Tooltip title="Leave blank to auto-infer from player history">
            <Info sx={{ ml: 0.5, fontSize: 12, color: 'text.secondary' }} />
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
          <Box sx={{ mt: 1.5 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Suggested teams for {formData.player_names?.[0]}:
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {teamSuggestions.map((team) => (
                <Chip
                  key={team}
                  label={team}
                  icon={<AutoAwesome sx={{ fontSize: 16 }} />}
                  onClick={() => applySuggestedTeam(team)}
                  size="small"
                  sx={{
                    background: 'rgba(63, 81, 181, 0.1)',
                    border: '1px solid rgba(63, 81, 181, 0.3)',
                    color: 'primary.main',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      background: 'rgba(63, 81, 181, 0.2)',
                      transform: 'scale(1.05)',
                    },
                  }}
                />
              ))}
            </Stack>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
              Click to select, or leave blank for auto-inference
            </Typography>
          </Box>
        )}
      </Box>

      {/* Opponent Selection */}
      <Box sx={{ mb: 1.5 }}>
        <Typography variant="body2" sx={{ mb: 1, display: 'flex', alignItems: 'center', fontWeight: 500 }}>
          <Group sx={{ mr: 0.5, color: 'secondary.main', fontSize: 16 }} />
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
      <Box sx={{ mb: 0 }}>
        <Typography variant="body2" sx={{ mb: 1, display: 'flex', alignItems: 'center', fontWeight: 500 }}>
          <CalendarToday sx={{ mr: 0.5, color: 'primary.main', fontSize: 16 }} />
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

    </Box>
  );
};