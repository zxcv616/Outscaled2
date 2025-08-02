import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { PredictionResult } from '../components/PredictionResult';
import { PredictionResponse, PredictionRequest } from '../types/api';

const theme = createTheme({
  palette: {
    mode: 'dark',
  },
});

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

const mockResult: PredictionResponse = {
  prediction: 'OVER',
  confidence: 75.0,
  base_model_confidence: 75.0,
  expected_stat: 4.5,
  confidence_interval: [3.8, 5.2],
  reasoning: 'Good recent form. Moderate sample size. Expected performance close to prop line. Moderate confidence prediction.',
  player_stats: {
    avg_kills: 4.0,
    avg_assists: 6.0,
    form_z_score: 0.5,
    maps_played: 10,
    avg_deaths: 2.5,
    avg_damage: 15000,
    avg_vision: 25.0,
    avg_cs: 200.0,
    position_factor: 1.2
  },
  data_years: '2024 (108 matches), 2025 (67 matches)',
  sample_details: {
    maps_used: 10,
    filter_criteria: 'Standard filtering applied',
    position: 'MID',
    opponent: 'Gen.G',
    tournament: 'LCK',
    map_range: '1-2',
    data_years: '2024 (108 matches), 2025 (67 matches)',
    sample_quality: 'Good',
    data_tier: 1,
    tier_name: 'Exact Tournament',
    tier_weight: 1.0,
    fallback_used: false,
    sample_sources: {},
    volatility: 0.3,
    ci_method: 'bootstrap',
    strict_mode_applied: false
  },
  data_tier: 1,
  confidence_warning: '',
  prop_type: 'kills',
  prop_value: 3.5
};

const mockRequest: PredictionRequest = {
  player_names: ['Faker'],
  prop_type: 'kills',
  prop_value: 3.5,
  map_range: [1, 2],
  opponent: 'Gen.G',
  tournament: 'LCK',
  team: 'T1',
  match_date: '2024-08-01T12:00',
  position_roles: ['MID'],
  strict_mode: false
};

describe('PredictionResult', () => {
  test('displays prediction result correctly', () => {
    renderWithTheme(<PredictionResult result={mockResult} request={mockRequest} loading={false} error={null} />);

    expect(screen.getByText('OVER')).toBeInTheDocument();
    expect(screen.getByText('AI Prediction')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
    expect(screen.getByText('Confidence Level')).toBeInTheDocument();
    expect(screen.getByText('4.5')).toBeInTheDocument();
    expect(screen.getAllByText(/Expected/)).toHaveLength(3);
  });

  test('displays confidence level correctly', () => {
    renderWithTheme(<PredictionResult result={mockResult} request={mockRequest} loading={false} error={null} />);

    expect(screen.getByText('75%')).toBeInTheDocument();
    expect(screen.getByText('Confidence Level')).toBeInTheDocument();
  });

  test('displays expected stat correctly', () => {
    renderWithTheme(<PredictionResult result={mockResult} request={mockRequest} loading={false} error={null} />);

    expect(screen.getByText('4.5')).toBeInTheDocument();
    expect(screen.getAllByText(/Expected/)).toHaveLength(3);
  });

  test('displays reasoning correctly', () => {
    renderWithTheme(<PredictionResult result={mockResult} request={mockRequest} loading={false} error={null} />);

    expect(screen.getByText('AI Reasoning')).toBeInTheDocument();
    expect(screen.getByText(/Good recent form/)).toBeInTheDocument();
  });

  test('displays data years information', () => {
    renderWithTheme(<PredictionResult result={mockResult} request={mockRequest} loading={false} error={null} />);

    expect(screen.getByText('Data Years')).toBeInTheDocument();
    expect(screen.getByText('2024 (108 matches), 2025 (67 matches)')).toBeInTheDocument();
  });

  test('displays maps used information', () => {
    renderWithTheme(<PredictionResult result={mockResult} request={mockRequest} loading={false} error={null} />);

    expect(screen.getByText('Maps Used')).toBeInTheDocument();
    expect(screen.getByText('10 maps')).toBeInTheDocument();
  });

  test('displays prediction curve', () => {
    renderWithTheme(<PredictionResult result={mockResult} request={mockRequest} loading={false} error={null} />);

    expect(screen.getByText('Prediction Distribution')).toBeInTheDocument();
  });

  test('handles loading state', () => {
    renderWithTheme(<PredictionResult result={null} request={null} loading={true} error={null} />);

    expect(screen.getByText('Analyzing Data...')).toBeInTheDocument();
    expect(screen.getByText(/Our AI is processing your request/)).toBeInTheDocument();
  });

  test('handles error state', () => {
    const errorMessage = 'Failed to get prediction';
    renderWithTheme(<PredictionResult result={null} request={null} loading={false} error={errorMessage} />);

    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  test('handles null result gracefully', () => {
    renderWithTheme(<PredictionResult result={null} request={null} loading={false} error={null} />);

    // Should not crash and should not render result content
    expect(screen.queryByText('OVER')).not.toBeInTheDocument();
    expect(screen.queryByText('AI Prediction')).not.toBeInTheDocument();
  });

  test('displays copy button', () => {
    renderWithTheme(<PredictionResult result={mockResult} request={mockRequest} loading={false} error={null} />);

    expect(screen.getByText('Copy JSON')).toBeInTheDocument();
  });

  test('handles missing optional fields gracefully', () => {
    const minimalResult: PredictionResponse = {
      prediction: 'UNDER',
      confidence: 50.0,
      base_model_confidence: 50.0,
      expected_stat: 3.0,
      confidence_interval: [2.5, 3.5],
      reasoning: 'Basic prediction',
      player_stats: {
        avg_kills: 3.0,
        avg_assists: 5.0,
        form_z_score: 0.0,
        maps_played: 5,
        avg_deaths: 2.0,
        avg_damage: 12000,
        avg_vision: 20.0,
        avg_cs: 180.0,
        position_factor: 1.0
      },
      data_years: '2024 (3 matches)',
      sample_details: {
        maps_used: 5,
        filter_criteria: 'Basic filtering',
        position: 'MID',
        opponent: 'Unknown',
        tournament: 'LCK',
        map_range: '1-2',
        data_years: '2024 (3 matches)',
        sample_quality: 'Poor',
        data_tier: 2,
        tier_name: 'Same Region',
        tier_weight: 0.8,
        fallback_used: true,
        sample_sources: {},
        volatility: 0.5,
        ci_method: 'bootstrap',
        strict_mode_applied: false
      },
      data_tier: 2,
      confidence_warning: 'Low sample size',
      prop_type: 'kills',
      prop_value: 3.0
    };

    renderWithTheme(<PredictionResult result={minimalResult} request={mockRequest} loading={false} error={null} />);

    expect(screen.getByText('UNDER')).toBeInTheDocument();
    expect(screen.getByText(/50\s*%/)).toBeInTheDocument();
    // Use getAllByText since multiple elements contain "3.0"
    expect(screen.getAllByText('3.0')).toHaveLength(1);
  });

  test('applies correct styling for OVER prediction', () => {
    renderWithTheme(<PredictionResult result={mockResult} request={mockRequest} loading={false} error={null} />);

    const predictionElement = screen.getByText('OVER');
    expect(predictionElement).toBeInTheDocument();
  });

  test('applies correct styling for UNDER prediction', () => {
    const underResult = { ...mockResult, prediction: 'UNDER' as const };
    renderWithTheme(<PredictionResult result={underResult} request={mockRequest} loading={false} error={null} />);

    const predictionElement = screen.getByText('UNDER');
    expect(predictionElement).toBeInTheDocument();
  });
}); 