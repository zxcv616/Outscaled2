import React, { useState, useCallback, useMemo } from 'react';
import {
  Autocomplete,
  TextField,
  Paper,
  Typography,
  Box,
  Chip,
  Avatar,
  CircularProgress,
  Fade,
  Popper,
  ClickAwayListener,
} from '@mui/material';
import {
  Search,
  Close,
  CheckCircle,
} from '@mui/icons-material';

interface EnhancedAutocompleteProps {
  options: string[];
  value?: string | string[] | null;
  onChange: (value: string | string[]) => void;
  loading?: boolean;
  multiple?: boolean;
  placeholder?: string;
  label?: string;
  error?: string;
  helpText?: string;
  disabled?: boolean;
  freeSolo?: boolean;
  groupBy?: (option: string) => string;
  renderOption?: (props: any, option: string) => React.ReactNode;
  filterOptions?: (options: string[], value: string) => string[];
}

const CustomPopper = (props: any) => {
  return (
    <Popper
      {...props}
      style={{
        ...props.style,
        zIndex: 1300,
      }}
      modifiers={[
        {
          name: 'flip',
          enabled: false,
        },
        {
          name: 'preventOverflow',
          enabled: true,
          options: {
            altAxis: true,
            altBoundary: true,
            tether: true,
            rootBoundary: 'document',
          },
        },
      ]}
    />
  );
};

const CustomPaper = (props: any) => {
  return (
    <Paper
      elevation={12}
      {...props}
      sx={{
        background: 'rgba(26, 26, 26, 0.98)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.15)',
        borderRadius: 2,
        mt: 1,
        overflow: 'hidden',
        maxHeight: 300,
        '& .MuiAutocomplete-listbox': {
          padding: 0,
          '& .MuiAutocomplete-option': {
            padding: '12px 16px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
            transition: 'all 0.2s ease',
            '&:hover': {
              background: 'rgba(63, 81, 181, 0.1)',
            },
            '&[aria-selected="true"]': {
              background: 'rgba(63, 81, 181, 0.2)',
              '&:hover': {
                background: 'rgba(63, 81, 181, 0.25)',
              },
            },
          },
        },
      }}
    />
  );
};

export const EnhancedAutocomplete: React.FC<EnhancedAutocompleteProps> = ({
  options,
  value,
  onChange,
  loading = false,
  multiple = false,
  placeholder,
  label,
  error,
  helpText,
  disabled = false,
  freeSolo = true,
  groupBy,
  renderOption,
  filterOptions,
}) => {
  const [inputValue, setInputValue] = useState('');
  const [focused, setFocused] = useState(false);
  const [touched, setTouched] = useState(false);
  const [open, setOpen] = useState(false);

  // Direct input change handling for immediate response
  const handleInputChange = useCallback((event: any, newInputValue: string) => {
    setInputValue(newInputValue);
  }, []);

  const handleChange = useCallback((event: any, newValue: any) => {
    if (multiple) {
      onChange(newValue || []);
    } else {
      onChange(newValue);
    }
    setTouched(true);
  }, [multiple, onChange]);

  const handleFocus = useCallback(() => {
    setFocused(true);
    setOpen(true);
    // Clear input to show all options on focus
    setInputValue('');
  }, []);

  const handleClick = useCallback(() => {
    if (!open) {
      setOpen(true);
      // Clear input value when opening to show all options
      if (!focused) {
        setInputValue('');
      }
    }
  }, [open, focused]);

  const handleBlur = useCallback(() => {
    setFocused(false);
    setTouched(true);
    setOpen(false);
  }, []);

  const filteredOptions = useMemo(() => {
    if (filterOptions) {
      return filterOptions(options, inputValue);
    }
    
    // Always show all options when input is empty or on first focus
    if (!inputValue || inputValue.trim() === '') {
      return options;
    }
    
    return options.filter((option) =>
      option.toLowerCase().includes(inputValue.toLowerCase())
    );
  }, [options, inputValue, filterOptions]);

  const showError = touched && Boolean(error);
  const showSuccess = touched && !error && value && (multiple ? (value as string[]).length > 0 : value);

  const getInputEndAdornment = () => {
    if (loading) {
      return <CircularProgress size={20} sx={{ color: 'primary.main' }} />;
    }
    
    if (showSuccess) {
      return <CheckCircle sx={{ color: 'success.main', fontSize: 20 }} />;
    }
    
    if (!focused && !value) {
      return <Search sx={{ color: 'text.secondary', fontSize: 20 }} />;
    }
    
    return null;
  };

  const renderDefaultOption = (props: any, option: string) => {
    const isSelected = multiple 
      ? (value as string[])?.includes(option)
      : value === option;

    return (
      <Box
        component="li"
        {...props}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          py: 1.5,
          px: 2,
        }}
      >
        <Avatar
          sx={{
            width: 32,
            height: 32,
            bgcolor: isSelected ? 'primary.main' : 'rgba(255, 255, 255, 0.1)',
            fontSize: '0.875rem',
            fontWeight: 600,
          }}
        >
          {option.charAt(0).toUpperCase()}
        </Avatar>
        <Box sx={{ flex: 1 }}>
          <Typography variant="body1" sx={{ fontWeight: 500 }}>
            {option}
          </Typography>
          {groupBy && (
            <Typography variant="caption" color="text.secondary">
              {groupBy(option)}
            </Typography>
          )}
        </Box>
        {isSelected && (
          <CheckCircle sx={{ color: 'primary.main', fontSize: 18 }} />
        )}
      </Box>
    );
  };

  const renderTags = (tagValue: string[], getTagProps: any) => {
    return tagValue.map((option, index) => (
      <Chip
        {...getTagProps({ index })}
        key={option}
        label={option}
        size="small"
        avatar={
          <Avatar sx={{ bgcolor: 'primary.main', fontSize: '0.75rem' }}>
            {option.charAt(0).toUpperCase()}
          </Avatar>
        }
        deleteIcon={<Close sx={{ fontSize: 16 }} />}
        sx={{
          background: 'rgba(63, 81, 181, 0.15)',
          border: '1px solid rgba(63, 81, 181, 0.3)',
          color: 'primary.main',
          fontWeight: 500,
          '& .MuiChip-deleteIcon': {
            color: 'rgba(63, 81, 181, 0.7)',
            '&:hover': {
              color: 'primary.main',
            },
          },
        }}
      />
    ));
  };

  return (
    <ClickAwayListener onClickAway={() => {
      setFocused(false);
      setOpen(false);
    }}>
      <Box sx={{ position: 'relative' }}>
        <Autocomplete
          multiple={multiple}
          freeSolo={freeSolo}
          options={filteredOptions}
          value={value}
          onChange={handleChange}
          onInputChange={handleInputChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onOpen={() => setOpen(true)}
          onClose={() => setOpen(false)}
          open={open}
          disabled={disabled}
          loading={loading}
          groupBy={groupBy}
          renderOption={renderOption || renderDefaultOption}
          renderTags={multiple ? renderTags : undefined}
          PopperComponent={CustomPopper}
          PaperComponent={CustomPaper}
          ChipProps={{
            size: 'small',
            variant: 'outlined',
          }}
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 2,
              transition: 'all 0.2s ease',
              '&:hover': {
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: showError ? 'error.main' : 'primary.main',
                },
              },
              '&.Mui-focused': {
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: showError ? 'error.main' : 'primary.main',
                  borderWidth: 2,
                },
              },
            },
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: showError 
                ? 'error.main' 
                : showSuccess 
                  ? 'success.main' 
                  : 'rgba(255, 255, 255, 0.3)',
              transition: 'border-color 0.2s ease',
            },
          }}
          renderInput={(params) => (
            <TextField
              {...params}
              label={label}
              placeholder={focused ? placeholder : ''}
              error={showError}
              helperText={showError ? error : helpText}
              onClick={handleClick}
              InputProps={{
                ...params.InputProps,
                endAdornment: (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getInputEndAdornment()}
                    {params.InputProps.endAdornment}
                  </Box>
                ),
              }}
              InputLabelProps={{
                ...params.InputLabelProps,
                shrink: true,
              }}
            />
          )}
        />

        {/* Loading Overlay */}
        {loading && (
          <Fade in={loading}>
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'rgba(26, 26, 26, 0.8)',
                backdropFilter: 'blur(4px)',
                borderRadius: 2,
                zIndex: 1,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CircularProgress size={16} sx={{ color: 'primary.main' }} />
                <Typography variant="caption" color="text.secondary">
                  Loading options...
                </Typography>
              </Box>
            </Box>
          </Fade>
        )}
      </Box>
    </ClickAwayListener>
  );
};