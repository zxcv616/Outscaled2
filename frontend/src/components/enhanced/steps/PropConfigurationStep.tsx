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
  { value: 'kills', label: 'Kills', icon: '⚔️', description: 'Player eliminations' },
  { value: 'assists', label: 'Assists', icon: '🤝', description: 'Team fight contributions' },
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
    <Box sx={{ py: 2 }}>
      {/* Header */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
          <TrendingUp sx={{ fontSize: 32, color: 'primary.main', mr: 1 }} />
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            Prop Configuration
          </Typography>
        </Box>
        <Typography variant="body1" color="text.secondary">
          Set up your prediction parameters and betting line
        </Typography>
      </Box>

      {/* Prop Type Selection */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
          <Analytics sx={{ mr: 1, color: 'primary.main' }} />
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
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
          <TrendingUp sx={{ color: 'secondary.main' }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Prop Value (O/U Line)
          </Typography>
          <Tooltip
            title="This is the betting line you're predicting over or under. The prediction will be based on TOTAL stats across your selected map range."
            placement="top"
            arrow
          >
            <Help sx={{ fontSize: 20, color: 'info.main', cursor: 'help' }} />
          </Tooltip>
        </Box>
        
        <Card
          sx={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
            p: 3,
          }}
        >
          <Box sx={{ mb: 3 }}>
            <TextField
              fullWidth
              label={`${currentPropType?.label || 'Prop'} Value`}
              type="number"
              value={propValueInput}
              onChange={handlePropValueChange}
              error={!!errors.prop_value}
              helperText={errors.prop_value || `Set the over/under line for TOTAL ${currentPropType?.label?.toLowerCase() || 'this prop'} across selected maps`}
              inputProps={{ 
                step: 0.5, 
                min: 0,
                max: 20,
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

          {/* Interactive Slider */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Adjust with slider:
            </Typography>
            <Slider
              value={propValueInput}
              onChange={handlePropValueSliderChange}
              min={0}
              max={15}
              step={0.5}
              marks={[
                { value: 0, label: '0' },
                { value: 5, label: '5' },
                { value: 10, label: '10' },
                { value: 15, label: '15' },
              ]}
              sx={{
                '& .MuiSlider-track': {
                  background: 'linear-gradient(45deg, #3f51b5, #f50057)',
                },
                '& .MuiSlider-thumb': {
                  background: 'linear-gradient(45deg, #3f51b5, #f50057)',
                },
              }}
            />
          </Box>

          {/* Suggested Values */}
          {suggestedValues.length > 0 && (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                💡 Popular {currentPropType?.label?.toLowerCase()} lines:
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {suggestedValues.map((value) => (
                  <Chip
                    key={value}
                    label={value}
                    onClick={() => applySuggestedValue(value)}
                    color={propValueInput === value ? 'primary' : 'default'}
                    sx={{
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
        </Card>
      </Box>

      {/* Map Range Configuration */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
          <SportsEsports sx={{ color: 'primary.main' }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Map Range - COMBINED Statistics
          </Typography>
          <Tooltip
            title="Map ranges calculate TOTAL stats across ALL selected maps. For example, 'Maps 1-2' means your total kills across Map 1 AND Map 2 combined, not individual map averages."
            placement="top"
            arrow
          >
            <Help sx={{ fontSize: 20, color: 'info.main', cursor: 'help' }} />
          </Tooltip>
        </Box>
        
        <Card
          sx={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
            p: 3,
          }}
        >
          {/* Important Alert about Combined Stats */}
          <Alert severity="info" sx={{ mb: 3, bgcolor: 'rgba(33, 150, 243, 0.1)', border: '1px solid rgba(33, 150, 243, 0.3)' }}>
            <Typography variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
              📊 COMBINED Statistics Calculation
            </Typography>
            <Typography variant="body2">
              Map ranges calculate <strong>TOTAL stats across ALL selected maps</strong>. 
              This is NOT an average - it's the sum of your performance across the entire map range.
            </Typography>
          </Alert>

          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
            <TextField
              label="Start Map"
              type="number"
              value={mapRange[0]}
              onChange={(e) => handleMapRangeChange('start', parseInt(e.target.value) || 1)}
              inputProps={{ min: 1, max: 5 }}
              sx={{ flex: 1 }}
            />
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography sx={{ fontWeight: 600, color: 'text.secondary' }}>to</Typography>
              <Add sx={{ color: 'primary.main', fontSize: 20 }} />
            </Box>
            <TextField
              label="End Map"
              type="number"
              value={mapRange[1]}
              onChange={(e) => handleMapRangeChange('end', parseInt(e.target.value) || 1)}
              inputProps={{ min: 1, max: 5 }}
              sx={{ flex: 1 }}
            />
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" sx={{ fontWeight: 500, mb: 1, color: 'primary.main' }}>
              📈 This prediction covers TOTAL {currentPropType?.label?.toLowerCase() || 'stats'} across Maps {mapRange[0]} to {mapRange[1]}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Example: If you get 3 {currentPropType?.label?.toLowerCase() || 'kills'} in Map {mapRange[0]} and 2 {currentPropType?.label?.toLowerCase() || 'kills'} in Map {mapRange[1]}, your combined total is 5 {currentPropType?.label?.toLowerCase() || 'kills'}.
            </Typography>
          </Box>

          <Box sx={{ bgcolor: 'rgba(255, 255, 255, 0.02)', p: 2, borderRadius: 2, border: '1px solid rgba(255, 255, 255, 0.1)' }}>
            <Typography variant="body2" sx={{ fontWeight: 500, mb: 2, color: 'secondary.main' }}>
              🎯 Maps Included in Combined Calculation:
            </Typography>
            <Stack spacing={1}>
              {Array.from({ length: mapRange[1] - mapRange[0] + 1 }, (_, i) => {
                const mapNumber = mapRange[0] + i;
                return (
                  <Box key={mapNumber} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Chip
                      label={`Map ${mapNumber}`}
                      size="small"
                      color="secondary"
                      variant="filled"
                      icon={<Add sx={{ fontSize: '16px !important' }} />}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {MAP_DESCRIPTIONS[mapNumber as keyof typeof MAP_DESCRIPTIONS]}
                    </Typography>
                  </Box>
                );
              })}
            </Stack>
            <Box sx={{ mt: 2, p: 2, bgcolor: 'rgba(76, 175, 80, 0.1)', borderRadius: 1, border: '1px solid rgba(76, 175, 80, 0.3)' }}>
              <Typography variant="body2" sx={{ fontWeight: 500, color: 'success.main' }}>
                ✅ Total Combined Range: {mapRange[1] - mapRange[0] + 1} map{mapRange[1] - mapRange[0] !== 0 ? 's' : ''}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Your {currentPropType?.label?.toLowerCase() || 'stats'} from ALL these maps will be added together for the final prediction.
              </Typography>
            </Box>
          </Box>
        </Card>
      </Box>

      {/* Advanced Settings */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
          <Settings sx={{ mr: 1, color: 'secondary.main' }} />
          Advanced Settings
        </Typography>
        
        <Card
          sx={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
            p: 3,
          }}
        >
          <FormControlLabel
            control={
              <Switch
                checked={formData.strict_mode || false}
                onChange={handleStrictModeChange}
                color="primary"
              />
            }
            label={
              <Box>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>
                  Strict Mode
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Use only exact tournament data (higher accuracy, may reduce available data)
                </Typography>
              </Box>
            }
          />
        </Card>
      </Box>

      {/* Prediction Summary */}
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
            Prediction Summary
          </Typography>
          
          <Stack spacing={2}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Prop Type:
              </Typography>
              <Chip
                label={currentPropType?.label || 'Not selected'}
                icon={<Typography sx={{ fontSize: '1rem' }}>{currentPropType?.icon}</Typography>}
                color="primary"
                variant="outlined"
              />
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Over/Under Line:
              </Typography>
              <Box sx={{ textAlign: 'right' }}>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  {propValueInput || 'Not set'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  (total {currentPropType?.label?.toLowerCase() || 'stats'} across all maps)
                </Typography>
              </Box>
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Map Range (Combined):
              </Typography>
              <Box sx={{ textAlign: 'right' }}>
                <Typography variant="body1" sx={{ fontWeight: 600, color: 'primary.main' }}>
                  Maps {mapRange[0]}-{mapRange[1]} TOTAL
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  ({mapRange[1] - mapRange[0] + 1} map{mapRange[1] - mapRange[0] !== 0 ? 's' : ''} combined)
                </Typography>
              </Box>
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Data Mode:
              </Typography>
              <Typography variant="body1" sx={{ fontWeight: 500 }}>
                {formData.strict_mode ? 'Strict (exact tournament only)' : 'Standard (all relevant data)'}
              </Typography>
            </Box>
            
            <Divider sx={{ my: 1 }} />
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Expected Confidence:
              </Typography>
              <Tooltip title="Estimated based on prop value and available data">
                <Typography 
                  variant="body2" 
                  sx={{ 
                    fontWeight: 500,
                    color: getConfidenceEstimate().includes('High') ? 'success.main' : 
                           getConfidenceEstimate().includes('Medium') ? 'warning.main' : 'text.secondary'
                  }}
                >
                  {getConfidenceEstimate()}
                </Typography>
              </Tooltip>
            </Box>
          </Stack>
        </CardContent>
      </Card>

      {/* Educational Note */}
      <Alert severity="info" icon={<Info />} sx={{ mt: 3, mb: 2, bgcolor: 'rgba(33, 150, 243, 0.1)', border: '1px solid rgba(33, 150, 243, 0.3)' }}>
        <Typography variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
          🤓 Betting Logic Reminder
        </Typography>
        <Typography variant="body2">
          This system predicts <strong>COMBINED/TOTAL statistics</strong> across your selected map range. 
          "Maps 1-2" means your total {currentPropType?.label?.toLowerCase() || 'stats'} from Map 1 + Map 2, not individual map performance or averages.
        </Typography>
      </Alert>

      {/* Final Validation */}
      {!formData.prop_value || formData.prop_value <= 0 ? (
        <Alert severity="warning" sx={{ mt: 2 }}>
          Please set a valid prop value to complete your prediction setup.
        </Alert>
      ) : (
        <Alert severity="success" sx={{ mt: 2 }}>
          ✅ Your prediction is ready! The AI will predict whether you'll go OVER or UNDER {formData.prop_value} total {currentPropType?.label?.toLowerCase() || 'stats'} across Maps {mapRange[0]}-{mapRange[1]}.
        </Alert>
      )}
    </Box>
  );
};