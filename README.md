# Outscaled2 - Enterprise League of Legends Prediction Platform

A production-ready, full-stack web application for predicting League of Legends player performance using advanced machine learning with comprehensive authentication, monitoring, and security features.

## ✨ Key Features

### Machine Learning & Predictions
- **Advanced ML Models**: Random Forest + XGBoost with calibrated probabilities
- **Confidence Intervals**: Statistical confidence calculations with gap-based adjustments
- **Prediction Curves**: Dynamic visualization of prediction probabilities across prop ranges
- **Position-Specific Analysis**: Tailored predictions based on player roles
- **Tiered Data System**: Weights data by relevance (Tier 1-5) for better accuracy

### Security & Authentication
- **JWT Authentication**: Secure access/refresh token system with Argon2 password hashing
- **API Key Management**: Secure API key generation and validation
- **Rate Limiting**: Redis-based rate limiting with in-memory fallback
- **Multi-Tier Subscriptions**: FREE, PRO, ENTERPRISE access levels
- **Security Headers**: Comprehensive security headers and CORS configuration
- **Password Security**: 50-bit minimum entropy validation and account lockout protection

### Enterprise Features
- **Real-time Monitoring**: Health checks and performance metrics
- **Caching System**: Redis-based caching with intelligent invalidation
- **Data Export**: CSV export functionality for predictions and analytics
- **Analytics Dashboard**: Comprehensive usage and performance analytics
- **Database Management**: SQLAlchemy with automatic migrations
- **Logging**: Structured logging with configurable levels

### User Experience
- **Modern React UI**: Material-UI v7 with dark theme
- **Multi-step Forms**: Intuitive prediction input with validation
- **Responsive Design**: Mobile-first responsive design patterns
- **Real-time Updates**: Live prediction updates and autocomplete
- **Accessibility**: WCAG 2.1 AA compliance

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Setup
1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Outscaled2
   ```

2. **Start the application**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 📁 Project Structure

```
Outscaled2/
├── backend/                 # Python FastAPI backend
│   ├── app/                # Application code
│   ├── data/               # Data files (ignored by Git)
│   ├── tests/              # Test files
│   └── requirements.txt    # Python dependencies
├── frontend/               # React TypeScript frontend
│   ├── src/                # Source code
│   ├── public/             # Static files
│   └── package.json        # Node.js dependencies
├── data/                   # Large datasets (ignored by Git)
├── docs/                   # Documentation
└── docker-compose.yml      # Docker configuration
```

## 🔐 Authentication & Security

### User Registration & Login
The platform includes a comprehensive authentication system:

```bash
# Register a new user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "SecurePassword123!"}'

# Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=SecurePassword123!"
```

### API Key Management
```bash
# Generate API key (requires authentication)
curl -X POST "http://localhost:8000/auth/api-keys" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My API Key", "tier": "PRO"}'
```

### Security Features
- **Password Requirements**: Minimum 50-bit entropy, complexity validation
- **Account Security**: Automatic lockout after failed attempts, IP-based blocking
- **JWT Security**: Secure secret key generation, configurable expiration
- **Rate Limiting**: Configurable limits per endpoint and user tier
- **Data Protection**: Secure password hashing with Argon2 (100MB memory cost)

## 🧪 Testing

### Backend Tests
```bash
cd backend
python run_tests.py                      # Run all backend tests
python run_confidence_tests.py quick     # Quick confidence test
python run_confidence_tests.py           # Full test suite
```

### Frontend Tests
```bash
cd frontend
npm test                                 # Run all frontend tests
npm test -- --coverage                  # Run with coverage report
```

### Authentication Tests
```bash
cd backend
python -m pytest tests/test_enhanced_auth.py -v    # Security tests
```

## 📊 Data Requirements

The application requires League of Legends match data in CSV format. Place your data files in:
- `data/` (root level)
- `backend/data/`

**Note**: Large CSV files are automatically ignored by Git to prevent repository bloat.

## 🚀 Production Deployment

### Environment Variables
Set the following environment variables for production:

```bash
# Backend (.env)
SECRET_KEY=your-256-bit-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost/outscaled
REDIS_URL=redis://localhost:6379
ENVIRONMENT=production

# Security
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_MIN_ENTROPY=50
MAX_LOGIN_ATTEMPTS=5

# Rate Limiting
RATE_LIMIT_LOGIN_MAX=5
RATE_LIMIT_LOGIN_WINDOW=300
RATE_LIMIT_API_FREE_MAX=60
RATE_LIMIT_API_PRO_MAX=1000

# Frontend (.env)
REACT_APP_API_URL=https://your-api-domain.com
REACT_APP_ENVIRONMENT=production
```

### Database Setup
```bash
# Initialize database with security fields
cd backend
python -c "from app.auth.migration_001_security_fields import run_migration; run_migration()"
```

### Production Build
```bash
# Build frontend
cd frontend
npm run build

# The build/ directory contains optimized production files
# Serve with nginx, Apache, or any static file server
```

### Docker Production
```bash
# Use production docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 Development

### Backend Development
```bash
cd backend
source venv/bin/activate  # If using virtual environment
pip install -r requirements.txt

# Install additional development dependencies
pip install pytest pytest-asyncio httpx

# Run development server
python -m uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install

# Start development server
npm start

# Run in development mode with hot reload
# Access at http://localhost:3000
```

### Database Development
```bash
# Create new migration
cd backend
python app/auth/create_migration.py "description_of_changes"

# Run migrations
python app/auth/run_migrations.py
```

## 📝 Git Configuration

### Ignored Files
The following files and directories are automatically ignored by Git:

#### Large Data Files
- `*.csv` - All CSV datasets
- `*.xlsx`, `*.xls` - Excel files
- `*.db`, `*.sqlite` - Database files
- `background.jpg` - Large images

#### Build Artifacts
- `node_modules/` - Node.js dependencies
- `__pycache__/` - Python cache
- `build/`, `dist/` - Build outputs
- `*.pyc` - Compiled Python files

#### Environment & Configuration
- `.env*` - Environment variables
- `secrets.json`, `credentials.json` - Sensitive data
- `config.ini` - Configuration files

#### IDE & OS Files
- `.vscode/`, `.idea/` - IDE settings
- `.DS_Store` - macOS files
- `Thumbs.db` - Windows files

#### Logs & Temporary Files
- `*.log` - Log files
- `*.tmp`, `*.temp` - Temporary files
- `coverage/` - Test coverage reports

### Adding Large Files
If you need to include large files that are currently ignored:

1. **Temporarily allow specific files**:
   ```bash
   git add -f path/to/specific/file.csv
   ```

2. **Create a data download script**:
   ```bash
   # Add to your README
   wget https://example.com/dataset.csv -O data/dataset.csv
   ```

## 🐳 Docker

### Services
- **Backend**: FastAPI application on port 8000
- **Frontend**: React application on port 3000

### Commands
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild containers
docker-compose up --build
```

## 🔍 API Documentation

### Interactive Documentation
Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs - Interactive API documentation
- **ReDoc**: http://localhost:8000/redoc - Alternative API documentation
- **Health Check**: http://localhost:8000/health - Service health status

### Core Endpoints

#### Predictions
```bash
POST /predict                    # Main prediction endpoint
GET /prediction-curve           # Generate prediction curve data
POST /check-data-availability   # Check if data exists for criteria
```

#### Data Access
```bash
GET /players                    # Get all available players
GET /teams                      # Get all available teams  
GET /tournaments                # Get all available tournaments
```

#### Authentication
```bash
POST /auth/register             # User registration
POST /auth/login                # User login
POST /auth/refresh              # Refresh access token
POST /auth/logout               # User logout
GET /auth/me                    # Get current user info
```

#### API Keys
```bash
POST /auth/api-keys             # Create new API key
GET /auth/api-keys              # List user's API keys
DELETE /auth/api-keys/{key_id}  # Delete API key
```

#### Analytics & Export
```bash
GET /analytics/dashboard        # Analytics dashboard data
POST /export/predictions        # Export predictions to CSV
GET /cache/stats                # Cache performance statistics
```

### Rate Limits
- **Free Tier**: 60 requests per minute
- **Pro Tier**: 1000 requests per minute  
- **Enterprise Tier**: 10000 requests per minute
- **Login Attempts**: 5 attempts per 5 minutes per IP

## 🧪 Confidence Calculation Fix

The application includes a comprehensive confidence calculation system that ensures consistency between top-level confidence and prediction curve confidence.

### Testing the Fix
```bash
cd backend
python run_confidence_tests.py quick
```

### Documentation
- `backend/TESTING_GUIDE.md` - Complete testing guide
- `backend/CONFIDENCE_FIX_SUMMARY.md` - Fix details

## 📚 Documentation

- `docs/` - Project documentation
- `backend/TESTING_GUIDE.md` - Testing instructions
- `backend/CONFIDENCE_FIX_SUMMARY.md` - Confidence fix details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

[Your License Here]

## 🆘 Troubleshooting

### Common Issues

**Backend won't start**:
```bash
docker logs outscaled2-backend-1
```

**Frontend build fails**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Large files not ignored**:
```bash
git rm --cached path/to/large/file
git commit -m "Remove large file from tracking"
```

### Data Setup
If you need to add new datasets:

1. Place CSV files in `data/` directory
2. Update data processing scripts in `backend/app/utils/`
3. Test with the confidence calculation tests

## 📞 Support

For issues or questions:
- Check the documentation in `docs/`
- Review the testing guides
- Check Docker logs for errors 