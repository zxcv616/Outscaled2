# Outscaled.GG Frontend

A modern React frontend for the Outscaled.GG League of Legends prop prediction platform.

## 🚀 Features

- **Modern UI**: Dark theme with Material-UI components
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Predictions**: Connect to the backend API for live predictions
- **Interactive Charts**: Visualize prediction data with Recharts
- **Form Validation**: Comprehensive input validation and error handling
- **TypeScript**: Full type safety throughout the application

## 🛠️ Tech Stack

- **React 19**: Latest React with hooks and functional components
- **TypeScript**: Type-safe development
- **Material-UI**: Professional UI components and theming
- **Recharts**: Interactive data visualization
- **Axios**: HTTP client for API communication

## 📦 Installation

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm start
   ```

3. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

## 🔧 Configuration

The frontend is configured to proxy API requests to the backend at `http://localhost:8000`. Make sure the backend is running before using the frontend.

### Environment Variables

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

## 📱 Usage

### Making Predictions

1. **Enter Player Names**: Add one or more player names (e.g., "Zika", "Scout")
2. **Select Prop Type**: Choose between "Kills" or "Assists"
3. **Set Prop Value**: Enter the betting line (e.g., 3.5 kills)
4. **Configure Map Range**: Select which maps to analyze (e.g., Maps 1-2)
5. **Fill Match Details**: Enter team, opponent, tournament, and date
6. **Select Positions**: Choose the player positions (e.g., TOP, MID)
7. **Get Prediction**: Click "Get Prediction" to receive AI analysis

### Understanding Results

The prediction result includes:

- **Prediction**: OVER or UNDER with confidence percentage
- **Expected Stat**: AI's predicted performance
- **Confidence Interval**: Statistical range of likely outcomes
- **AI Reasoning**: Detailed explanation of the prediction
- **Player Statistics**: Historical performance data
- **Visual Charts**: Graphical representation of predictions

## 🎨 UI Components

### Header
- Outscaled.GG branding with analytics icon
- Beta status indicator
- Responsive design for mobile

### Prediction Form
- Multi-step form with validation
- Autocomplete for player names
- Dropdown selectors for options
- Real-time error feedback

### Prediction Result
- Large prediction chip (OVER/UNDER)
- Confidence progress bar
- Statistical cards with key metrics
- Interactive bar chart
- Detailed player statistics grid
- AI reasoning explanation

## 🔄 API Integration

The frontend communicates with the backend through:

- **POST /predict**: Submit prediction requests
- **GET /health**: Check API health status

### Request Format
```typescript
{
  player_names: string[];
  prop_type: 'kills' | 'assists';
  prop_value: number;
  map_range: [number, number];
  opponent: string;
  tournament: string;
  team: string;
  match_date: string;
  position_roles: string[];
}
```

### Response Format
```typescript
{
  prediction: 'OVER' | 'UNDER';
  confidence: number;
  expected_stat: number;
  confidence_interval: [number, number];
  reasoning: string;
  player_stats: PlayerStats;
  data_years: string;
}
```

## 🚀 Development

### Available Scripts

- `npm start`: Start development server
- `npm run build`: Build for production
- `npm test`: Run test suite
- `npm run eject`: Eject from Create React App

### Project Structure

```
src/
├── components/
│   ├── Header.tsx           # App header with branding
│   ├── PredictionForm.tsx   # Main prediction form
│   └── PredictionResult.tsx # Results display
├── services/
│   └── api.ts              # API communication
├── types/
│   └── api.ts              # TypeScript interfaces
├── App.tsx                 # Main app component
└── index.tsx               # App entry point
```

## 🎯 Features in Detail

### Form Validation
- Required field validation
- Numeric range validation
- Date format validation
- Real-time error display

### Responsive Design
- Mobile-first approach
- Breakpoint-based layouts
- Touch-friendly controls
- Optimized for all screen sizes

### Dark Theme
- Professional dark color scheme
- High contrast for readability
- Consistent Material-UI theming
- Accessible color choices

### Error Handling
- Network error display
- API error messages
- Loading states
- Graceful fallbacks

## 🔒 Security

- Input sanitization
- CORS configuration
- HTTPS in production
- Secure API communication

## 📊 Performance

- Lazy loading of components
- Optimized bundle size
- Efficient re-renders
- Minimal API calls

## 🧪 Testing

Run the test suite:

```bash
npm test
```

## 🚀 Deployment

### Build for Production

```bash
npm run build
```

### Docker Deployment

The frontend can be deployed with Docker:

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `npm test`
5. Submit a pull request

## 📄 License

This project is proprietary software for Outscaled.GG.

---

**Note**: Make sure the backend API is running on `http://localhost:8000` before using the frontend.
