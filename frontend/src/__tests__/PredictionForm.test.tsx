import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { PredictionForm } from '../components/PredictionForm';

// Mock the API module
jest.mock('../services/api', () => ({
  predictionApi: {
    getPlayers: jest.fn().mockResolvedValue({
      players: ['Player1', 'Player2', 'Faker', 'Gumayusi']
    }),
    getTeams: jest.fn().mockResolvedValue({
      teams: ['Team1', 'Team2', 'T1', 'Gen.G']
    }),
    getTournaments: jest.fn().mockResolvedValue({
      tournaments: ['LCK', 'LPL', 'LCS', 'LEC']
    }),
    predict: jest.fn().mockResolvedValue({
      prediction: 'OVER',
      confidence: 75.5,
      expected_stat: 3.2,
      reasoning: 'Test reasoning'
    })
  }
}));

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('PredictionForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders form elements', async () => {
    renderWithTheme(<PredictionForm onSubmit={mockOnSubmit} loading={false} />);

    // Wait for form to load
    await waitFor(() => {
      expect(screen.getByLabelText(/player names/i)).toBeInTheDocument();
    });

    // Check for basic form elements
    expect(screen.getByLabelText(/prop value/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/opponent/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /get ai prediction/i })).toBeInTheDocument();
  });

  test('shows validation error for empty prop value', async () => {
    const user = userEvent.setup();
    renderWithTheme(<PredictionForm onSubmit={mockOnSubmit} loading={false} />);

    // Wait for form to load
    await waitFor(() => {
      expect(screen.getByLabelText(/player names/i)).toBeInTheDocument();
    });

    // Submit form without filling required fields
    const submitButton = screen.getByRole('button', { name: /get ai prediction/i });
    await user.click(submitButton);

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText('Prop value must be greater than 0')).toBeInTheDocument();
    });
  });

  test('handles autocomplete selection', async () => {
    const user = userEvent.setup();
    renderWithTheme(<PredictionForm onSubmit={mockOnSubmit} loading={false} />);

    // Wait for form to load
    await waitFor(() => {
      expect(screen.getByLabelText(/player names/i)).toBeInTheDocument();
    });

    // Test player autocomplete
    const playerInput = screen.getByLabelText(/player names/i);
    await user.click(playerInput);
    await user.keyboard('Player1');
    await user.keyboard('{Enter}');

    // Verify player was added
    await waitFor(() => {
      expect(screen.getByText('Player1')).toBeInTheDocument();
    });
  });

  test('handles form reset', async () => {
    const user = userEvent.setup();
    renderWithTheme(<PredictionForm onSubmit={mockOnSubmit} loading={false} />);

    // Wait for form to load
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /get ai prediction/i })).toBeInTheDocument();
    });

    // Fill in a field
    const propValueInput = screen.getByLabelText(/prop value/i);
    await user.clear(propValueInput);
    await user.type(propValueInput, '5.0');

    // Verify field has value
    expect(propValueInput).toHaveValue(5);

    // Clear the field
    await user.clear(propValueInput);
    await user.type(propValueInput, '0');

    // Verify field is reset
    expect(propValueInput).toHaveValue(0);
  });

  test('shows loading state', () => {
    renderWithTheme(<PredictionForm onSubmit={mockOnSubmit} loading={true} />);

    // Should show loading text
    expect(screen.getByText('Getting Prediction...')).toBeInTheDocument();
  });

  test('handles API errors gracefully', async () => {
    // Mock API to throw error
    const { predictionApi } = require('../services/api');
    predictionApi.getPlayers.mockRejectedValueOnce(new Error('API Error'));

    renderWithTheme(<PredictionForm onSubmit={mockOnSubmit} loading={false} />);

    // Should still render form even with API error
    await waitFor(() => {
      expect(screen.getByLabelText(/player names/i)).toBeInTheDocument();
    });
  });

  test('team field is optional', async () => {
    const user = userEvent.setup();
    renderWithTheme(<PredictionForm onSubmit={mockOnSubmit} loading={false} />);

    // Wait for form to load
    await waitFor(() => {
      expect(screen.getByLabelText(/player names/i)).toBeInTheDocument();
    });

    // Check that team field shows as optional
    const teamField = screen.getByLabelText(/team \(optional/i);
    expect(teamField).toBeInTheDocument();

    // Fill in required fields
    const playerInput = screen.getByLabelText(/player names/i);
    await user.click(playerInput);
    await user.keyboard('Player1');
    await user.keyboard('{Enter}');

    const propValueInput = screen.getByLabelText(/prop value/i);
    await user.clear(propValueInput);
    await user.type(propValueInput, '3.5');

    const opponentInput = screen.getByLabelText(/opponent/i);
    await user.click(opponentInput);
    await user.keyboard('Team2');
    await user.keyboard('{Enter}');

    // Submit form without filling team field
    const submitButton = screen.getByRole('button', { name: /get ai prediction/i });
    await user.click(submitButton);

    // Should not show team validation error
    await waitFor(() => {
      expect(screen.queryByText(/team is required/i)).not.toBeInTheDocument();
    });
  });
}); 