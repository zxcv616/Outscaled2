import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import PredictionCurve from '../components/PredictionCurve';
import { PredictionCurvePoint } from '../types/api';

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

const mockCurveData: PredictionCurvePoint[] = [
  {
    prop_value: 2.5,
    prediction: 'OVER',
    confidence: 85.2,
    expected_stat: 4.2,
    is_input_prop: false
  },
  {
    prop_value: 3.0,
    prediction: 'OVER',
    confidence: 78.1,
    expected_stat: 4.2,
    is_input_prop: false
  },
  {
    prop_value: 3.5,
    prediction: 'OVER',
    confidence: 65.3,
    expected_stat: 4.2,
    is_input_prop: false
  },
  {
    prop_value: 4.0,
    prediction: 'UNDER',
    confidence: 45.7,
    expected_stat: 4.2,
    is_input_prop: true
  },
  {
    prop_value: 4.5,
    prediction: 'UNDER',
    confidence: 72.8,
    expected_stat: 4.2,
    is_input_prop: false
  },
  {
    prop_value: 5.0,
    prediction: 'UNDER',
    confidence: 89.1,
    expected_stat: 4.2,
    is_input_prop: false
  }
];

describe('PredictionCurve', () => {
  it('renders prediction curve with data', () => {
    renderWithTheme(
      <PredictionCurve curve={mockCurveData} inputPropValue={4.0} />
    );

    expect(screen.getByText('Prediction Confidence Landscape')).toBeInTheDocument();
    expect(screen.getByText(/How the model's prediction and confidence change around your prop line/)).toBeInTheDocument();
  });

  it('displays table headers correctly', () => {
    renderWithTheme(
      <PredictionCurve curve={mockCurveData} inputPropValue={4.0} />
    );

    expect(screen.getByText('Prop Value')).toBeInTheDocument();
    expect(screen.getByText('Prediction')).toBeInTheDocument();
    expect(screen.getByText('Confidence')).toBeInTheDocument();
    expect(screen.getByText('Expected Stat')).toBeInTheDocument();
    expect(screen.getByText('Gap')).toBeInTheDocument();
  });

  it('displays all curve points in table', () => {
    renderWithTheme(
      <PredictionCurve curve={mockCurveData} inputPropValue={4.0} />
    );

    // Check that the table structure is rendered
    expect(screen.getByText('Prop Value')).toBeInTheDocument();
    expect(screen.getByText('Prediction')).toBeInTheDocument();
    expect(screen.getByText('Confidence')).toBeInTheDocument();
    
    // Check that we have some data rendered
    expect(screen.getByText('2.5')).toBeInTheDocument();
    
    // Check that we have multiple OVER and UNDER predictions
    const overPredictions = screen.getAllByText('OVER');
    const underPredictions = screen.getAllByText('UNDER');
    expect(overPredictions.length).toBeGreaterThan(0);
    expect(underPredictions.length).toBeGreaterThan(0);
  });

  it('highlights the input prop value', () => {
    renderWithTheme(
      <PredictionCurve curve={mockCurveData} inputPropValue={4.0} />
    );

    expect(screen.getByText('Your Line')).toBeInTheDocument();
  });

  it('displays OVER and UNDER predictions correctly', () => {
    renderWithTheme(
      <PredictionCurve curve={mockCurveData} inputPropValue={4.0} />
    );

    const overPredictions = screen.getAllByText('OVER');
    const underPredictions = screen.getAllByText('UNDER');
    
    expect(overPredictions.length).toBeGreaterThan(0);
    expect(underPredictions.length).toBeGreaterThan(0);
  });

  it('displays confidence percentages', () => {
    renderWithTheme(
      <PredictionCurve curve={mockCurveData} inputPropValue={4.0} />
    );

    expect(screen.getByText('85.2%')).toBeInTheDocument();
    expect(screen.getByText('78.1%')).toBeInTheDocument();
    expect(screen.getByText('45.7%')).toBeInTheDocument();
  });

  it('displays expected stat values', () => {
    renderWithTheme(
      <PredictionCurve curve={mockCurveData} inputPropValue={4.0} />
    );

    // Should display 4.2 for all rows
    const expectedStatElements = screen.getAllByText('4.2');
    expect(expectedStatElements.length).toBeGreaterThan(0);
  });

  it('displays key insights section', () => {
    renderWithTheme(
      <PredictionCurve curve={mockCurveData} inputPropValue={4.0} />
    );

    expect(screen.getByText('Key Insights:')).toBeInTheDocument();
    expect(screen.getByText(/The prediction flips from OVER to UNDER at around/)).toBeInTheDocument();
    expect(screen.getByText(/Confidence remains consistent across the range/)).toBeInTheDocument();
    expect(screen.getByText(/Expected performance: 4.2/)).toBeInTheDocument();
  });

  it('handles empty curve data gracefully', () => {
    const { container } = renderWithTheme(
      <PredictionCurve curve={[]} inputPropValue={4.0} />
    );

    expect(container.firstChild).toBeNull();
  });

  it('handles null curve data gracefully', () => {
    const { container } = renderWithTheme(
      <PredictionCurve curve={null as any} inputPropValue={4.0} />
    );

    expect(container.firstChild).toBeNull();
  });

  it('calculates and displays gap values correctly', () => {
    renderWithTheme(
      <PredictionCurve curve={mockCurveData} inputPropValue={4.0} />
    );

    // Gap should be |expected_stat - prop_value|
    // For prop_value 2.5, gap should be |4.2 - 2.5| = 1.7
    expect(screen.getByText('1.7')).toBeInTheDocument();
    // For prop_value 4.0, gap should be |4.2 - 4.0| = 0.2
    expect(screen.getByText('0.2')).toBeInTheDocument();
  });
}); 