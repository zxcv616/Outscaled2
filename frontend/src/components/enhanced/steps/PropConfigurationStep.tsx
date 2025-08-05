import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Card,
  CardContent,
  Alert,
  Chip,
  Stack,
  Divider,
  Switch,
  FormControlLabel,
  Tooltip,
} from '@mui/material';
import {
  TrendingUp,
  SportsEsports,
  Info,
  Settings,
  Analytics,
  Add,
  Help,
} from '@mui/icons-material';

interface PropConfigurationStepProps {
  formData: any;
  errors: Record<string, string>;
  onChange: (updates: any) => void;
}

const PROP_TYPES = [
  { value: 'kills', label: 'Kills', icon: 'K', description: 'Player eliminations' },
  { value: 'assists', label: 'Assists', icon: 'A', description: 'Team fight contributions' },
];

const MAP_DESCRIPTIONS = {
  1: 'Game 1 - Opening match',
  2: 'Game 2 - Standard match',
  3: 'Game 3 - Decisive match',
  4: 'Game 4 - Extended series',
  5: 'Game 5 - Final match',
};

export const PropConfigurationStep: React.FC<PropConfigurationStepProps> = ({
  formData,
  errors,
  onChange,
}) => {
  const [propValueInput, setPropValueInput] = useState(formData.prop_value || 2.5);
  const [suggestedValues, setSuggestedValues] = useState<number[]>([]);

  // Generate suggested prop values based on prop type
  useEffect(() => {
    const generateSuggestions = () => {
      const propType = formData.prop_type || 'kills';
      let suggestions: number[] = [];
      
      if (propType === 'kills') {
        suggestions = [1.5, 2.5, 3.5, 4.5, 5.5];
      } else if (propType === 'assists') {
        suggestions = [2.5, 3.5, 4.5, 5.5, 6.5];
      }
      
      setSuggestedValues(suggestions);
      
      // Auto-suggest a reasonable default if no value set
      if (!formData.prop_value && suggestions.length > 0) {
        const defaultValue = suggestions[Math.floor(suggestions.length / 2)];
        setPropValueInput(defaultValue);
        onChange({ prop_value: defaultValue });
      }
    };

    generateSuggestions();
  }, [formData.prop_type, formData.prop_value, onChange]);

  const handlePropTypeChange = (event: any) => {
    const newPropType = event.target.value;
    onChange({ prop_type: newPropType });
  };

  const handlePropValueChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(event.target.value) || 0;
    setPropValueInput(value);
    onChange({ prop_value: value });
  };

  const handlePropValueSliderChange = (event: Event, newValue: number | number[]) => {
    const value = Array.isArray(newValue) ? newValue[0] : newValue;
    setPropValueInput(value);
    onChange({ prop_value: value });
  };

  const handleMapRangeChange = (field: 'start' | 'end', value: number) => {
    const currentRange = formData.map_range || [1, 2];
    const newRange = field === 'start' 
      ? [value, Math.max(value, currentRange[1])]
      : [currentRange[0], Math.max(currentRange[0], value)];
    
    onChange({ map_range: newRange });
  };

  const handleStrictModeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ strict_mode: event.target.checked });
  };

  const applySuggestedValue = (value: number) => {
    setPropValueInput(value);
    onChange({ prop_value: value });
  };

  const getConfidenceEstimate = () => {
    // Simple heuristic for confidence estimation
    const hasAllData = formData.player_names?.length > 0 && 
                      formData.tournament && 
                      formData.opponent && 
                      formData.prop_value > 0;
    
    if (!hasAllData) return 'Incomplete data';
    
    const propValue = formData.prop_value || 0;
    const propType = formData.prop_type || 'kills';
    
    // Rough confidence based on prop value reasonableness
    if (propType === 'kills' && propValue >= 1 && propValue <= 6) {
      return 'High confidence expected';
    } else if (propType === 'assists' && propValue >= 2 && propValue <= 8) {
      return 'High confidence expected';
    } else if (propValue > 0 && propValue <= 15) {
      return 'Medium confidence expected';
    } else {
      return 'Low confidence - unusual prop value';
    }
  };

  const currentPropType = PROP_TYPES.find(type => type.value === formData.prop_type);
  const mapRange = formData.map_range || [1, 2];

  return (
    <Box>

      {/* Prop Type Selection */}
      <Box sx={{ mb: 1.5 }}>
        <Typography variant="body2" sx={{ mb: 1, display: 'flex', alignItems: 'center', fontWeight: 500 }}>
          <Analytics sx={{ mr: 0.5, color: 'primary.main', fontSize: 16 }} />
          Prop Type
        </Typography>
        
        <FormControl fullWidth>
          <InputLabel>Prop Type</InputLabel>
          <Select
            value={formData.prop_type || 'kills'}
            label="Prop Type"
            onChange={handlePropTypeChange}
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
            {PROP_TYPES.map((type) => (
              <MenuItem key={type.value} value={type.value}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography component="span" sx={{ fontSize: '1.2rem' }}>
                    {type.icon}
                  </Typography>
                  <Box>
                    <Typography sx={{ fontWeight: 500 }}>
                      {type.label}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {type.description}
                    </Typography>
                  </Box>
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* Prop Value Configuration */}
      <Box sx={{ mb: 1.5 }}>
        <Typography variant="body2" sx={{ mb: 1, display: 'flex', alignItems: 'center', fontWeight: 500 }}>
          <TrendingUp sx={{ mr: 0.5, color: 'secondary.main', fontSize: 16 }} />
          Prop Value (O/U Line)
        </Typography>
        
        <Box sx={{ p: 1.5, background: 'rgba(255, 255, 255, 0.03)', borderRadius: 1.5 }}>
          <TextField
            fullWidth
            label={`${currentPropType?.label || 'Prop'} Value`}
            type="number"
            value={propValueInput}
            onChange={handlePropValueChange}
            error={!!errors.prop_value}
            helperText={errors.prop_value || 'Over/under line'}
            inputProps={{ step: 0.5, min: 0, max: 20 }}
            size="small"
          />
          
          {suggestedValues.length > 0 && (
            <Stack direction="row" spacing={0.5} sx={{ mt: 1 }} flexWrap="wrap" useFlexGap>
              {suggestedValues.map((value) => (
                <Chip
                  key={value}
                  label={value}
                  onClick={() => applySuggestedValue(value)}
                  color={propValueInput === value ? 'primary' : 'default'}
                  size="small"
                  sx={{ cursor: 'pointer' }}
                />
              ))}
            </Stack>
          )}
        </Box>
      </Box>

      {/* Map Range Configuration */}
      <Box sx={{ mb: 1.5 }}>
        <Typography variant="body2" sx={{ mb: 1, display: 'flex', alignItems: 'center', fontWeight: 500 }}>
          <SportsEsports sx={{ mr: 0.5, color: 'primary.main', fontSize: 16 }} />
          Map Range (Combined Stats)
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center' }}>
          <TextField
            label="Start Map"
            type="number"
            value={mapRange[0]}
            onChange={(e) => handleMapRangeChange('start', parseInt(e.target.value) || 1)}
            inputProps={{ min: 1, max: 5 }}
            size="small"
            sx={{ flex: 1 }}
          />
          <Typography variant="body2" color="text.secondary">to</Typography>
          <TextField
            label="End Map"
            type="number"
            value={mapRange[1]}
            onChange={(e) => handleMapRangeChange('end', parseInt(e.target.value) || 1)}
            inputProps={{ min: 1, max: 5 }}
            size="small"
            sx={{ flex: 1 }}
          />
        </Box>
      </Box>

      {/* Advanced Settings */}
      <Box sx={{ mb: 0 }}>
        <FormControlLabel
          control={
            <Switch
              checked={formData.strict_mode || false}
              onChange={handleStrictModeChange}
              color="primary"
              size="small"
            />
          }
          label={
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              Strict Mode
            </Typography>
          }
        />
      </Box>

    </Box>
  );
};