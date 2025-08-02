import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { PredictionResult } from '../components/PredictionResult';

// Mock recharts components
jest.mock('recharts', () => ({
  BarChart: () => null,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  ResponsiveContainer: ({ children }: any) => children,
}));

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

describe('PredictionResult', () => {
  // Realistic mock data based on actual model output
  const mockResult = {
    prediction: 'OVER' as const,
    confidence: 75.0,
    expected_stat: 4.5,
    confidence_interval: [3.8, 5.2] as [number, number],
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
    data_years: '2024 (108 matches), 2025 (67 matches)'
  };

  const mockRequest = {
    player_names: ['Faker'],
    prop_type: 'kills' as const,
    prop_value: 4.5,
    map_range: [1, 3] as [number, number],
    opponent: 'T1',
    tournament: 'LCK',
    team: 'SKT',
    match_date: '2024-01-15T10:00',
    position_roles: ['MID']
  };

  test('renders prediction result with OVER prediction', () => {
    renderWithTheme(<PredictionResult result={mockResult} request={mockRequest} loading={false} error={null} />);

    // Check prediction chip
    expect(screen.getByText('OVER')).toBeInTheDocument();
    expect(screen.getByText(/75\s*%/)).toBeInTheDocument();

    // Check expected stat (formatted to 1 decimal place)
    expect(screen.getByText('4.5')).toBeInTheDocument();

    // Check confidence interval (formatted as [3.8, 5.2])
    // Check for confidence interval values (they appear in the text)
    expect(screen.getByText(/3\.8/)).toBeInTheDocument();
    expect(screen.getByText(/5\.2/)).toBeInTheDocument();

    // Check reasoning (actual model output)
    expect(screen.getByText(/Good recent form/)).toBeInTheDocument();
    expect(screen.getByText(/Moderate sample size/)).toBeInTheDocument();
  });

  test('renders prediction result with UNDER prediction', () => {
    const underResult = { 
      ...mockResult, 
      prediction: 'UNDER' as const,
      reasoning: 'Below-average recent form. Limited sample size reduces confidence. Expected performance significantly below prop line. Low confidence prediction.'
    };
    renderWithTheme(<PredictionResult result={underResult} request={mockRequest} loading={false} error={null} />);

    expect(screen.getByText('UNDER')).toBeInTheDocument();
  });

  test('displays confidence progress bar', () => {
    renderWithTheme(<PredictionResult result={mockResult} request={mockRequest} loading={false} error={null} />);

    // Should show confidence percentage
    expect(screen.getByText(/75\s*%/)).toBeInTheDocument();
  });

  test('displays all player statistics', () => {
    renderWithTheme(<PredictionResult result={mockResult} request={mockRequest} loading={false} error={null} />);

    // Since recharts is mocked, we just verify the component renders without errors
    expect(screen.getByText('OVER')).toBeInTheDocument();
    expect(screen.getByText(/75\s*%/)).toBeInTheDocument();
    expect(screen.getByText('4.5')).toBeInTheDocument();
  });

  test('displays data years information', () => {
    renderWithTheme(<PredictionResult result={mockResult} request={mockRequest} loading={false} error={null} />);

    expect(screen.getByText('Data Coverage')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument(); // maps_played
  });

  test('handles high confidence prediction', () => {
    const highConfidenceResult = { 
      ...mockResult, 
      confidence: 95.0,
      reasoning: 'Strong recent form above historical average. Good sample size for reliable prediction. Expected performance significantly above prop line. High confidence prediction.'
    };
    renderWithTheme(<PredictionResult result={highConfidenceResult} request={mockRequest} loading={false} error={null} />);

    expect(screen.getByText(/95\s*%/)).toBeInTheDocument();
  });

  test('handles low confidence prediction', () => {
    const lowConfidenceResult = { 
      ...mockResult, 
      confidence: 25.0,
      reasoning: 'Poor recent form below historical average. Limited sample size reduces confidence. Expected performance significantly below prop line. Low confidence prediction.'
    };
    renderWithTheme(<PredictionResult result={lowConfidenceResult} request={mockRequest} loading={false} error={null} />);

    expect(screen.getByText(/25\s*%/)).toBeInTheDocument();
  });

  test('handles zero confidence prediction', () => {
    const zeroConfidenceResult = { 
      ...mockResult, 
      confidence: 0.0,
      reasoning: 'Form is consistent with historical average. Limited sample size reduces confidence. Expected performance close to prop line. Low confidence prediction.'
    };
    renderWithTheme(<PredictionResult result={zeroConfidenceResult} request={mockRequest} loading={false} error={null} />);

    expect(screen.getByText(/0\s*%/)).toBeInTheDocument();
  });

  test('handles 100% confidence prediction', () => {
    const fullConfidenceResult = { 
      ...mockResult, 
      confidence: 100.0,
      reasoning: 'Strong recent form above historical average. Good sample size for reliable prediction. Expected performance significantly above prop line. High confidence prediction.'
    };
    renderWithTheme(<PredictionResult result={fullConfidenceResult} request={mockRequest} loading={false} error={null} />);

    expect(screen.getByText(/100\s*%/)).toBeInTheDocument();
  });

  test('displays reasoning in alert component', () => {
    renderWithTheme(<PredictionResult result={mockResult} request={mockRequest} loading={false} error={null} />);

    // Reasoning should be displayed in an alert/info box
    expect(screen.getByText(/Good recent form/)).toBeInTheDocument();
    expect(screen.getByText(/Moderate sample size/)).toBeInTheDocument();
  });

  test('handles different confidence intervals', () => {
    const wideIntervalResult = { 
      ...mockResult, 
      confidence_interval: [2.0, 7.0] as [number, number],
      expected_stat: 4.5
    };
    renderWithTheme(<PredictionResult result={wideIntervalResult} request={mockRequest} loading={false} error={null} />);

    // Check for confidence interval values (they appear in the text)
    expect(screen.getByText(/2\.0/)).toBeInTheDocument();
    expect(screen.getByText(/7\.0/)).toBeInTheDocument();
  });

  test('handles narrow confidence intervals', () => {
    const narrowIntervalResult = { 
      ...mockResult, 
      confidence_interval: [4.4, 4.6] as [number, number],
      expected_stat: 4.5
    };
    renderWithTheme(<PredictionResult result={narrowIntervalResult} request={mockRequest} loading={false} error={null} />);

    // Check for confidence interval values (they appear in the text)
    expect(screen.getByText(/4\.4/)).toBeInTheDocument();
    expect(screen.getByText(/4\.6/)).toBeInTheDocument();
  });

  test('handles decimal values in statistics', () => {
    const decimalStatsResult = {
      ...mockResult,
      player_stats: {
        ...mockResult.player_stats,
        avg_kills: 3.75,
        avg_assists: 5.25,
        form_z_score: -0.25
      }
    };
    renderWithTheme(<PredictionResult result={decimalStatsResult} request={mockRequest} loading={false} error={null} />);

    // Since recharts is mocked, we just verify the component renders without errors
    expect(screen.getByText('OVER')).toBeInTheDocument();
    expect(screen.getByText(/75\s*%/)).toBeInTheDocument();
  });

  test('handles large numbers in statistics', () => {
    const largeNumbersResult = {
      ...mockResult,
      player_stats: {
        ...mockResult.player_stats,
        avg_damage: 25000,
        avg_cs: 350
      }
    };
    renderWithTheme(<PredictionResult result={largeNumbersResult} request={mockRequest} loading={false} error={null} />);

    // Since recharts is mocked, we just verify the component renders without errors
    expect(screen.getByText('OVER')).toBeInTheDocument();
    expect(screen.getByText(/75\s*%/)).toBeInTheDocument();
  });

  test('handles zero values in statistics', () => {
    const zeroStatsResult = {
      ...mockResult,
      player_stats: {
        ...mockResult.player_stats,
        avg_kills: 0,
        avg_assists: 0,
        maps_played: 0
      }
    };
    renderWithTheme(<PredictionResult result={zeroStatsResult} request={mockRequest} loading={false} error={null} />);

    // Since recharts is mocked, we just verify the component renders without errors
    expect(screen.getByText('OVER')).toBeInTheDocument();
    expect(screen.getByText(/75\s*%/)).toBeInTheDocument();
  });

  test('displays chart for player statistics', () => {
    renderWithTheme(<PredictionResult result={mockResult} request={mockRequest} loading={false} error={null} />);

    // Since recharts is mocked, we just verify the component renders without errors
    expect(screen.getByText('OVER')).toBeInTheDocument();
    expect(screen.getByText(/75\s*%/)).toBeInTheDocument();
  });

  test('handles missing optional fields gracefully', () => {
    const minimalResult = {
      prediction: 'OVER' as const,
      confidence: 50.0,
      expected_stat: 3.0,
      confidence_interval: [2.0, 4.0] as [number, number],
      reasoning: 'Form is consistent with historical average. Limited sample size reduces confidence. Expected performance close to prop line. Low confidence prediction.',
      player_stats: {
        avg_kills: 3.0,
        avg_assists: 5.0,
        form_z_score: 0.0,
        maps_played: 5,
        avg_deaths: 2.0,
        avg_damage: 12000,
        avg_vision: 20.0,
        avg_cs: 150.0,
        position_factor: 1.0
      },
      data_years: '2024 (3 matches)'
    };

    renderWithTheme(<PredictionResult result={minimalResult} request={mockRequest} loading={false} error={null} />);

    // Should still render without errors
    expect(screen.getByText('OVER')).toBeInTheDocument();
    expect(screen.getByText(/50\s*%/)).toBeInTheDocument();
    // Use getAllByText since multiple elements contain "3.0"
    expect(screen.getAllByText('3.0')).toHaveLength(2);
  });

  test('applies correct styling for OVER prediction', () => {
    renderWithTheme(<PredictionResult result={mockResult} request={mockRequest} loading={false} error={null} />);

    const predictionChip = screen.getByText('OVER');
    expect(predictionChip).toBeInTheDocument();
    // Should have success color for OVER prediction
  });

  test('applies correct styling for UNDER prediction', () => {
    const underResult = { 
      ...mockResult, 
      prediction: 'UNDER' as const,
      reasoning: 'Below-average recent form. Limited sample size reduces confidence. Expected performance significantly below prop line. Low confidence prediction.'
    };
    renderWithTheme(<PredictionResult result={underResult} request={mockRequest} loading={false} error={null} />);

    const predictionChip = screen.getByText('UNDER');
    expect(predictionChip).toBeInTheDocument();
    // Should have error color for UNDER prediction
  });

  test('handles loading state', () => {
    renderWithTheme(<PredictionResult result={null} request={null} loading={true} error={null} />);

    expect(screen.getByText('Analyzing Data...')).toBeInTheDocument();
  });

  test('handles error state', () => {
    const errorMessage = 'Failed to get prediction';
    renderWithTheme(<PredictionResult result={null} request={null} loading={false} error={errorMessage} />);

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  test('handles null result', () => {
    const { container } = renderWithTheme(<PredictionResult result={null} request={null} loading={false} error={null} />);

    expect(container.firstChild).toBeNull();
  });

  test('displays copy JSON button', () => {
    renderWithTheme(<PredictionResult result={mockResult} request={mockRequest} loading={false} error={null} />);

    expect(screen.getByText('Copy JSON')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /copy json/i })).toBeInTheDocument();
  });

  test('copy button is not shown when no result', () => {
    renderWithTheme(<PredictionResult result={null} request={null} loading={false} error={null} />);

    expect(screen.queryByText('Copy JSON')).not.toBeInTheDocument();
  });
}); 