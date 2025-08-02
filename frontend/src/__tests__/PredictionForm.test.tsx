import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { PredictionForm } from '../components/PredictionForm';
import { PredictionRequest } from '../types/api';

// Mock the API service with realistic responses
jest.mock('../services/api', () => ({
  predictionApi: {
    getPlayers: jest.fn().mockResolvedValue({ 
      players: ['Player1', 'Player2', 'Player3', 'Player4', 'Player5'] 
    }),
    getTeams: jest.fn().mockResolvedValue({ 
      teams: ['Team1', 'Team2', 'Team3', 'Team4', 'Team5'] 
    }),
    getTournaments: jest.fn().mockResolvedValue({ 
      tournaments: ['LPL', 'LCK', 'LEC', 'LCS', 'MSI', 'Worlds', 'LDL', 'PCS', 'VCS', 'KeSPA'] 
    }),
    getPrediction: jest.fn().mockResolvedValue({
      prediction: 'OVER',
      confidence: 75.0,
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
      data_years: '2024 (108 matches), 2025 (67 matches)'
    })
  }
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

describe('PredictionForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders form with all required fields', async () => {
    renderWithTheme(<PredictionForm onSubmit={mockOnSubmit} loading={false} />);

    // Wait for autocomplete data to load
    await waitFor(() => {
      expect(screen.getByLabelText(/player names/i)).toBeInTheDocument();
    });

    // Check for all required form fields
    expect(screen.getByLabelText(/player names/i)).toBeInTheDocument();
    // Use getAllByText since multiple elements contain "Prop Type"
    expect(screen.getAllByText(/prop type/i)).toHaveLength(2);
    expect(screen.getByLabelText(/prop value/i)).toBeInTheDocument();
    // Use getAllByText since multiple elements contain these labels
    expect(screen.getAllByText(/map start/i)).toHaveLength(2);
    expect(screen.getAllByText(/map end/i)).toHaveLength(2);
    expect(screen.getByLabelText(/team/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/opponent/i)).toBeInTheDocument();
    // Use getAllByText since multiple elements contain "Tournament"
    expect(screen.getAllByText(/tournament/i)).toHaveLength(2);
    expect(screen.getByLabelText(/match date/i)).toBeInTheDocument();
    // Use getAllByText since multiple elements contain "Position Roles"
    expect(screen.getAllByText(/position roles/i)).toHaveLength(2);
    expect(screen.getByRole('button', { name: /get prediction/i })).toBeInTheDocument();
  });

  test('validates required fields', async () => {
    const user = userEvent.setup();
    renderWithTheme(<PredictionForm onSubmit={mockOnSubmit} loading={false} />);

    // Wait for form to load
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /get prediction/i })).toBeInTheDocument();
    });

    // Try to submit without filling required fields
    const submitButton = screen.getByRole('button', { name: /get prediction/i });
    await user.click(submitButton);

    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByText(/at least one player is required/i)).toBeInTheDocument();
      expect(screen.getByText(/prop value must be greater than 0/i)).toBeInTheDocument();
      expect(screen.getByText(/team is required/i)).toBeInTheDocument();
      expect(screen.getByText(/opponent is required/i)).toBeInTheDocument();
    });
  });

  test('validates prop value format', async () => {
    const user = userEvent.setup();
    renderWithTheme(<PredictionForm onSubmit={mockOnSubmit} loading={false} />);

    // Wait for form to load
    await waitFor(() => {
      expect(screen.getByLabelText(/prop value/i)).toBeInTheDocument();
    });

    // Enter invalid prop value and submit to trigger validation
    const propValueInput = screen.getByLabelText(/prop value/i);
    await user.clear(propValueInput);
    await user.type(propValueInput, '0');

    // Submit form to trigger validation
    const submitButton = screen.getByRole('button', { name: /get prediction/i });
    await user.click(submitButton);

    // Should show validation error - use exact text from component
    await waitFor(() => {
      expect(screen.getByText('Prop value must be greater than 0')).toBeInTheDocument();
    });
  });

  test('submits form successfully', async () => {
    const user = userEvent.setup();
    renderWithTheme(<PredictionForm onSubmit={mockOnSubmit} loading={false} />);

    // Wait for form to load and tournaments to be populated
    await waitFor(() => {
      expect(screen.getByLabelText(/player names/i)).toBeInTheDocument();
    });

    // Wait for tournaments to be loaded
    await waitFor(() => {
      const allComboboxes = screen.getAllByRole('combobox');
      expect(allComboboxes.length).toBeGreaterThan(0);
    });

    // Fill form with valid data
    const playerInput = screen.getByLabelText(/player names/i);
    await user.click(playerInput);
    await user.type(playerInput, 'Player1');
    await user.keyboard('{Enter}');

    const propValueInput = screen.getByLabelText(/prop value/i);
    await user.clear(propValueInput);
    await user.type(propValueInput, '5');

    const teamInput = screen.getByLabelText(/team/i);
    await user.click(teamInput);
    await user.type(teamInput, 'Team1');
    await user.keyboard('{Enter}');

    const opponentInput = screen.getByLabelText(/opponent/i);
    await user.click(opponentInput);
    await user.type(opponentInput, 'Team2');
    await user.keyboard('{Enter}');

    // Fill in match date (required field)
    const matchDateInput = screen.getByLabelText(/match date/i);
    await user.clear(matchDateInput);
    await user.type(matchDateInput, '2024-01-15T10:00');

    // Select tournament (required field) - use getAllByRole to find the tournament select
    const allComboboxes = screen.getAllByRole('combobox');
    const tournamentSelect = allComboboxes[2]; // Third combobox is tournament
    await user.click(tournamentSelect);
    await user.keyboard('{ArrowDown}');
    await user.keyboard('{Enter}');

    // Select position roles (required field) - use the last combobox which is the position roles select
    const positionRolesSelect = allComboboxes[allComboboxes.length - 1]; // Last combobox is position roles
    await user.click(positionRolesSelect);
    await user.keyboard('{ArrowDown}');
    await user.keyboard('{Enter}');

    // Close the dropdown menu by pressing Escape
    await user.keyboard('{Escape}');

    // Wait for form to be ready and submit button to be enabled
    await waitFor(() => {
      const submitButton = screen.getByRole('button', { name: /get prediction/i });
      expect(submitButton).toBeEnabled();
    });

    const submitButton = screen.getByRole('button', { name: /get prediction/i });
    await user.click(submitButton);

    // Should call onSubmit with valid data - using real validation
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(expect.objectContaining({
        player_names: ['Player1'],
        prop_value: 5,
        team: 'Team1',
        opponent: 'Team2',
        position_roles: expect.arrayContaining([expect.any(String)])
      }));
    }, { timeout: 5000 });
  });

  test('handles loading state', () => {
    renderWithTheme(<PredictionForm onSubmit={mockOnSubmit} loading={true} />);

    expect(screen.getByRole('button', { name: /getting prediction/i })).toBeDisabled();
    expect(screen.getByText(/getting prediction/i)).toBeInTheDocument();
  });

  test('handles API errors gracefully', async () => {
    const user = userEvent.setup();
    
    // Mock API error
    const { predictionApi } = require('../services/api');
    predictionApi.getPlayers.mockRejectedValueOnce(new Error('API Error'));

    renderWithTheme(<PredictionForm onSubmit={mockOnSubmit} loading={false} />);

    // Should still render form even if API calls fail
    await waitFor(() => {
      expect(screen.getByLabelText(/player names/i)).toBeInTheDocument();
    });
  });
}); 