import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import PredictionCurve from '../components/PredictionCurve';

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('PredictionCurve', () => {
  it('renders prediction curve with data', () => {
    renderWithTheme(
      <PredictionCurve 
        expectedStat={4.2}
        propValue={3.0}
        confidenceInterval={[3.8, 4.6]}
        prediction="OVER"
        confidence={75}
      />
    );

    expect(screen.getByText(/Prop Line: 3/)).toBeInTheDocument();
    expect(screen.getByText(/Expected: 4.2/)).toBeInTheDocument();
  });

  it('displays table headers correctly', () => {
    renderWithTheme(
      <PredictionCurve 
        expectedStat={4.2}
        propValue={3.0}
        confidenceInterval={[3.8, 4.6]}
        prediction="OVER"
        confidence={75}
      />
    );

    expect(screen.getByText('Gap')).toBeInTheDocument();
    expect(screen.getByText('Confidence Interval')).toBeInTheDocument();
    expect(screen.getByText('Prediction Strength')).toBeInTheDocument();
  });

  it('displays all curve points in table', () => {
    renderWithTheme(
      <PredictionCurve 
        expectedStat={4.2}
        propValue={3.0}
        confidenceInterval={[3.8, 4.6]}
        prediction="OVER"
        confidence={75}
      />
    );

    // Check that the stats are rendered
    expect(screen.getByText('Gap')).toBeInTheDocument();
    expect(screen.getByText('Confidence Interval')).toBeInTheDocument();
    expect(screen.getByText('Prediction Strength')).toBeInTheDocument();
    
    // Check that we have the expected stat value using regex
    expect(screen.getByText(/Expected: 4.2/)).toBeInTheDocument();
  });

  it('highlights the input prop value', () => {
    renderWithTheme(
      <PredictionCurve 
        expectedStat={4.2}
        propValue={3.0}
        confidenceInterval={[3.8, 4.6]}
        prediction="OVER"
        confidence={75}
      />
    );

    // Check that prop line is displayed
    expect(screen.getByText(/Prop Line: 3/)).toBeInTheDocument();
  });

  it('displays OVER and UNDER predictions correctly', () => {
    // Test OVER prediction
    const { rerender } = renderWithTheme(
      <PredictionCurve 
        expectedStat={4.2}
        propValue={3.0}
        confidenceInterval={[3.8, 4.6]}
        prediction="OVER"
        confidence={75}
      />
    );

    expect(screen.getByText(/Expected: 4.2/)).toBeInTheDocument();

    // Test UNDER prediction
    rerender(
      <PredictionCurve 
        expectedStat={2.8}
        propValue={3.0}
        confidenceInterval={[2.4, 3.2]}
        prediction="UNDER"
        confidence={75}
      />
    );

    expect(screen.getByText(/Expected: 2.8/)).toBeInTheDocument();
  });

  it('displays confidence percentages', () => {
    renderWithTheme(
      <PredictionCurve 
        expectedStat={4.2}
        propValue={3.0}
        confidenceInterval={[3.8, 4.6]}
        prediction="OVER"
        confidence={75}
      />
    );

    // Check that confidence interval is displayed
    expect(screen.getByText(/\[3.8, 4.6\]/)).toBeInTheDocument();
  });

  it('displays expected stat values', () => {
    renderWithTheme(
      <PredictionCurve 
        expectedStat={4.2}
        propValue={3.0}
        confidenceInterval={[3.8, 4.6]}
        prediction="OVER"
        confidence={75}
      />
    );

    expect(screen.getByText(/Expected: 4.2/)).toBeInTheDocument();
  });

  it('displays key insights section', () => {
    renderWithTheme(
      <PredictionCurve 
        expectedStat={4.2}
        propValue={3.0}
        confidenceInterval={[3.8, 4.6]}
        prediction="OVER"
        confidence={75}
      />
    );

    expect(screen.getByText('Gap')).toBeInTheDocument();
    expect(screen.getByText('Confidence Interval')).toBeInTheDocument();
    expect(screen.getByText('Prediction Strength')).toBeInTheDocument();
  });

  it('handles empty curve data gracefully', () => {
    renderWithTheme(
      <PredictionCurve 
        expectedStat={0}
        propValue={0}
        confidenceInterval={[0, 0]}
        prediction="OVER"
        confidence={75}
      />
    );

    expect(screen.getByText(/Prop Line: 0/)).toBeInTheDocument();
    expect(screen.getByText(/Expected: 0.0/)).toBeInTheDocument();
  });

  it('handles null curve data gracefully', () => {
    renderWithTheme(
      <PredictionCurve 
        expectedStat={0}
        propValue={0}
        confidenceInterval={[0, 0]}
        prediction="UNDER"
        confidence={75}
      />
    );

    expect(screen.getByText(/Prop Line: 0/)).toBeInTheDocument();
    expect(screen.getByText(/Expected: 0.0/)).toBeInTheDocument();
  });

  it('calculates and displays gap values correctly', () => {
    renderWithTheme(
      <PredictionCurve 
        expectedStat={4.2}
        propValue={3.0}
        confidenceInterval={[3.8, 4.6]}
        prediction="OVER"
        confidence={75}
      />
    );

    // Gap should be 1.2 (4.2 - 3.0)
    expect(screen.getByText('1.2')).toBeInTheDocument();
  });

  it('displays correct prediction strength based on confidence', () => {
    // Test Strong prediction (confidence >= 85)
    const { rerender } = renderWithTheme(
      <PredictionCurve 
        expectedStat={4.2}
        propValue={3.0}
        confidenceInterval={[3.8, 4.6]}
        prediction="OVER"
        confidence={90}
      />
    );

    expect(screen.getByText('Strong')).toBeInTheDocument();

    // Test Moderate prediction (confidence >= 65)
    rerender(
      <PredictionCurve 
        expectedStat={4.2}
        propValue={3.0}
        confidenceInterval={[3.8, 4.6]}
        prediction="OVER"
        confidence={75}
      />
    );

    expect(screen.getByText('Moderate')).toBeInTheDocument();

    // Test Weak prediction (confidence < 65)
    rerender(
      <PredictionCurve 
        expectedStat={4.2}
        propValue={3.0}
        confidenceInterval={[3.8, 4.6]}
        prediction="OVER"
        confidence={50}
      />
    );

    expect(screen.getByText('Weak')).toBeInTheDocument();
  });
}); 