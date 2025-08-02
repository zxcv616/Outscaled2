# Outscaled2 - League of Legends Prediction Platform

A full-stack web application for predicting League of Legends player performance using machine learning.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

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

## 🧪 Testing

### Backend Tests
```bash
cd backend
python run_confidence_tests.py quick    # Quick confidence test
python run_confidence_tests.py          # Full test suite
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📊 Data Requirements

The application requires League of Legends match data in CSV format. Place your data files in:
- `data/` (root level)
- `backend/data/`

**Note**: Large CSV files are automatically ignored by Git to prevent repository bloat.

## 🔧 Development

### Backend Development
```bash
cd backend
source venv/bin/activate  # If using virtual environment
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm start
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

Once the backend is running, visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

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