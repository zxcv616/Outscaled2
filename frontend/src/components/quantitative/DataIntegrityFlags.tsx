import React from 'react';
import {
  Box,
  Typography,
  Chip,
  Alert,
} from '@mui/material';
import {
  CheckCircle,
  Warning,
  Error,
  Info,
  Security,
} from '@mui/icons-material';
import { PredictionResponse } from '../../types/api';

interface DataIntegrityFlagsProps {
  result: PredictionResponse;
}

const DataIntegrityFlags: React.FC<DataIntegrityFlagsProps> = ({ result }) => {
  const flags = generateIntegrityFlags(result);

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Security sx={{ mr: 1, color: 'success.main' }} />
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Data Integrity Status
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 3 }}>
        {flags.map((flag, index) => (
          <Chip
            key={index}
            icon={flag.icon}
            label={flag.label}
            color={flag.color}
            variant={flag.severity === 'error' ? 'filled' : 'outlined'}
            size="medium"
          />
        ))}
      </Box>

      {flags.some(flag => flag.severity === 'warning') && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Some data quality issues detected. Review the flags above for details.
        </Alert>
      )}

      {flags.some(flag => flag.severity === 'error') && (
        <Alert severity="error">
          Critical data integrity issues found. Use predictions with extreme caution.
        </Alert>
      )}
    </Box>
  );
};

interface IntegrityFlag {
  label: string;
  icon: React.ReactElement;
  color: 'success' | 'warning' | 'error' | 'info';
  severity: 'success' | 'warning' | 'error' | 'info';
}

function generateIntegrityFlags(result: PredictionResponse): IntegrityFlag[] {
  const flags: IntegrityFlag[] = [];
  const sampleSize = result.sample_details?.maps_used || 0;
  const volatility = result.sample_details?.volatility || 0.3;

  // Sample size checks
  if (sampleSize >= 20) {
    flags.push({
      label: `Excellent Sample Size (${sampleSize} maps)`,
      icon: <CheckCircle />,
      color: 'success',
      severity: 'success'
    });
  } else if (sampleSize >= 10) {
    flags.push({
      label: `Good Sample Size (${sampleSize} maps)`,
      icon: <Info />,
      color: 'info',
      severity: 'info'
    });
  } else if (sampleSize >= 5) {
    flags.push({
      label: `Limited Sample Size (${sampleSize} maps)`,
      icon: <Warning />,
      color: 'warning',
      severity: 'warning'
    });
  } else {
    flags.push({
      label: `Very Limited Sample (${sampleSize} maps)`,
      icon: <Error />,
      color: 'error',
      severity: 'error'
    });
  }

  // Fallback data check
  if (result.sample_details?.fallback_used) {
    flags.push({
      label: 'Fallback Data Used',
      icon: <Warning />,
      color: 'warning',
      severity: 'warning'
    });
  } else {
    flags.push({
      label: 'Direct Match Data',
      icon: <CheckCircle />,
      color: 'success',
      severity: 'success'
    });
  }

  // Strict mode check
  if (result.sample_details?.strict_mode_applied) {
    flags.push({
      label: 'Strict Mode Applied',
      icon: <CheckCircle />,
      color: 'success',
      severity: 'success'
    });
  } else {
    flags.push({
      label: 'Relaxed Filtering',
      icon: <Info />,
      color: 'info',
      severity: 'info'
    });
  }

  // Volatility check
  if (volatility < 0.2) {
    flags.push({
      label: 'Low Volatility',
      icon: <CheckCircle />,
      color: 'success',
      severity: 'success'
    });
  } else if (volatility < 0.4) {
    flags.push({
      label: 'Moderate Volatility',
      icon: <Info />,
      color: 'info',
      severity: 'info'
    });
  } else if (volatility < 0.6) {
    flags.push({
      label: 'High Volatility',
      icon: <Warning />,
      color: 'warning',
      severity: 'warning'
    });
  } else {
    flags.push({
      label: 'Extreme Volatility',
      icon: <Error />,
      color: 'error',
      severity: 'error'
    });
  }

  // Tier status
  if (result.sample_details?.tier_name) {
    flags.push({
      label: `Tier: ${result.sample_details.tier_name}`,
      icon: <Info />,
      color: 'info',
      severity: 'info'
    });
  }

  // Confidence interval method
  if (result.sample_details?.ci_method) {
    flags.push({
      label: `CI Method: ${result.sample_details.ci_method}`,
      icon: <Info />,
      color: 'info',
      severity: 'info'
    });
  }

  return flags;
}

export default DataIntegrityFlags;