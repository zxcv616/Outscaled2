# 🧪 Testing Guide for Outscaled.GG

This guide covers comprehensive testing for both backend and frontend components of the Outscaled.GG platform.

## 📋 Table of Contents

- [Backend Testing](#backend-testing)
- [Frontend Testing](#frontend-testing)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Test Structure](#test-structure)
- [Continuous Integration](#continuous-integration)

---

## 🐍 Backend Testing

### **Test Structure**
```
backend/
├── tests/
│   ├── __init__.py
│   ├── test_data_processor.py    # Data processing tests
│   ├── test_prediction_model.py  # Model prediction tests
│   └── test_api.py              # API endpoint tests
└── run_tests.py                 # Test runner script
```

### **Test Categories**

#### **1. DataProcessor Tests** (`test_data_processor.py`)
- **Data Loading**: Tests CSV file loading and concatenation
- **Data Preprocessing**: Tests data cleaning and transformation
- **Feature Engineering**: Tests statistical feature generation
- **Player/Team Filtering**: Tests data filtering logic
- **Autocomplete Data**: Tests player and team name extraction
- **Error Handling**: Tests graceful error handling

#### **2. PredictionModel Tests** (`test_prediction_model.py`)
- **Model Initialization**: Tests model setup and training
- **Feature Preparation**: Tests input feature processing
- **Prediction Logic**: Tests OVER/UNDER predictions
- **Confidence Calculation**: Tests confidence scoring
- **Reasoning Generation**: Tests AI reasoning output
- **Edge Cases**: Tests boundary conditions
- **Consistency**: Tests prediction stability

#### **3. API Tests** (`test_api.py`)
- **Endpoint Testing**: Tests all API endpoints
- **Request Validation**: Tests input validation
- **Response Formatting**: Tests response structure
- **Error Handling**: Tests error responses
- **Authentication**: Tests security measures
- **Documentation**: Tests API docs generation

### **Running Backend Tests**

```bash
# Navigate to backend directory
cd backend

# Install test dependencies
pip install -r requirements.txt

# Run all tests
python run_tests.py

# Run specific test file
python -m pytest tests/test_data_processor.py -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

---

## ⚛️ Frontend Testing

### **Test Structure**
```
frontend/src/__tests__/
├── PredictionForm.test.tsx      # Form component tests
├── PredictionResult.test.tsx    # Results component tests
└── api.test.ts                 # API service tests
```

### **Test Categories**

#### **1. PredictionForm Tests** (`PredictionForm.test.tsx`)
- **Component Rendering**: Tests form field display
- **Autocomplete Functionality**: Tests player/team selection
- **Form Validation**: Tests input validation
- **User Interactions**: Tests form submission
- **Loading States**: Tests loading indicators
- **Error Handling**: Tests API error scenarios
- **Multi-select**: Tests multiple player selection

#### **2. PredictionResult Tests** (`PredictionResult.test.tsx`)
- **Result Display**: Tests prediction output
- **Confidence Visualization**: Tests confidence display
- **Statistics Charts**: Tests data visualization
- **Edge Cases**: Tests boundary conditions
- **Styling**: Tests component styling
- **Responsive Design**: Tests layout adaptation

#### **3. API Service Tests** (`api.test.ts`)
- **API Calls**: Tests HTTP requests
- **Response Handling**: Tests data processing
- **Error Scenarios**: Tests network failures
- **Request Validation**: Tests input validation
- **Response Validation**: Tests output validation

### **Running Frontend Tests**

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in CI mode
npm run test:ci

# Run specific test file
npm test -- PredictionForm.test.tsx
```

---

## 🚀 Running Tests

### **Quick Start**

```bash
# Backend Tests
cd backend
python run_tests.py

# Frontend Tests
cd frontend
npm test
```

### **Full Test Suite**

```bash
# Run all backend tests
cd backend
python run_tests.py

# Run all frontend tests
cd frontend
npm run test:coverage

# Run integration tests
docker-compose up --build
curl http://localhost:8000/health
curl http://localhost:3000
```

### **Test Commands**

#### **Backend Commands**
```bash
# Unit tests
python -m pytest tests/ -v

# Specific module
python -m pytest tests/test_data_processor.py -v

# With coverage
python -m pytest tests/ --cov=app --cov-report=html

# FastAPI test client
python -m pytest tests/test_api.py -v
```

#### **Frontend Commands**
```bash
# All tests
npm test

# Coverage report
npm run test:coverage

# Watch mode
npm test -- --watch

# Specific test
npm test -- --testNamePattern="PredictionForm"
```

---

## 📊 Test Coverage

### **Backend Coverage Targets**
- **DataProcessor**: 95%+ coverage
- **PredictionModel**: 90%+ coverage
- **API Endpoints**: 100% coverage
- **Error Handling**: 100% coverage

### **Frontend Coverage Targets**
- **Components**: 90%+ coverage
- **API Service**: 95%+ coverage
- **User Interactions**: 85%+ coverage
- **Error Scenarios**: 100% coverage

### **Coverage Reports**

```bash
# Backend coverage
cd backend
python -m pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html

# Frontend coverage
cd frontend
npm run test:coverage
# Open coverage/lcov-report/index.html
```

---

## 🏗️ Test Structure

### **Backend Test Patterns**

```python
# Test class structure
class TestDataProcessor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        pass
    
    def test_specific_functionality(self):
        """Test specific functionality"""
        # Arrange
        # Act
        # Assert
        pass
    
    def test_edge_case(self):
        """Test edge cases"""
        pass
    
    def test_error_handling(self):
        """Test error scenarios"""
        pass
```

### **Frontend Test Patterns**

```typescript
// Test suite structure
describe('ComponentName', () => {
  const mockProps = {};
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  test('renders correctly', () => {
    // Arrange
    // Act
    // Assert
  });
  
  test('handles user interaction', async () => {
    // Test user interactions
  });
  
  test('handles errors gracefully', () => {
    // Test error scenarios
  });
});
```

---

## 🔄 Continuous Integration

### **GitHub Actions Workflow**

```yaml
name: Tests
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          python run_tests.py

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          npm install
      - name: Run tests
        run: |
          cd frontend
          npm run test:ci
```

### **Pre-commit Hooks**

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## 🧪 Test Categories

### **Unit Tests**
- **Backend**: Individual class and method testing
- **Frontend**: Component and service testing
- **Coverage**: 90%+ code coverage target

### **Integration Tests**
- **API Testing**: End-to-end API testing
- **Component Integration**: Frontend component interaction
- **Data Flow**: Backend to frontend data flow

### **End-to-End Tests**
- **User Workflows**: Complete user journey testing
- **Cross-browser**: Multiple browser testing
- **Performance**: Load and stress testing

---

## 📈 Test Metrics

### **Backend Metrics**
- **Test Count**: 50+ unit tests
- **Coverage**: 95%+ code coverage
- **Performance**: <2s test execution time
- **Reliability**: 100% test pass rate

### **Frontend Metrics**
- **Test Count**: 30+ component tests
- **Coverage**: 90%+ code coverage
- **Performance**: <5s test execution time
- **Reliability**: 100% test pass rate

---

## 🛠️ Test Utilities

### **Backend Test Utilities**

```python
# Mock data generators
def create_mock_player_data():
    return pd.DataFrame({
        'playername': ['Player1', 'Player2'],
        'teamname': ['Team1', 'Team2'],
        'kills': [5, 3],
        'assists': [8, 6]
    })

# Test fixtures
@pytest.fixture
def sample_request():
    return {
        'player_names': ['Player1'],
        'prop_type': 'kills',
        'prop_value': 5.0
    }
```

### **Frontend Test Utilities**

```typescript
// Mock API responses
const mockPredictionResponse = {
  prediction: 'OVER',
  confidence: 75.0,
  expected_stat: 4.5
};

// Test renderers
const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};
```

---

## 🎯 Best Practices

### **Test Writing Guidelines**
1. **Arrange-Act-Assert**: Clear test structure
2. **Descriptive Names**: Meaningful test names
3. **Single Responsibility**: One assertion per test
4. **Mock External Dependencies**: Isolate units
5. **Test Edge Cases**: Cover boundary conditions

### **Test Maintenance**
1. **Regular Updates**: Keep tests current
2. **Refactoring**: Update tests with code changes
3. **Documentation**: Document complex test scenarios
4. **Performance**: Monitor test execution time

### **Test Organization**
1. **Logical Grouping**: Group related tests
2. **Clear Hierarchy**: Organize test suites
3. **Consistent Naming**: Follow naming conventions
4. **Modular Structure**: Separate test concerns

---

## 🚨 Troubleshooting

### **Common Issues**

#### **Backend Test Issues**
```bash
# Import errors
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"

# Missing dependencies
pip install -r requirements.txt

# Data file issues
# Ensure test data is available
```

#### **Frontend Test Issues**
```bash
# Jest configuration
# Check jest.config.js

# Mock issues
# Verify mock implementations

# Environment variables
# Set REACT_APP_API_URL for tests
```

### **Debug Commands**
```bash
# Backend debugging
python -m pytest tests/ -v -s --tb=long

# Frontend debugging
npm test -- --verbose --no-coverage
```

---

## 📚 Additional Resources

- **Backend Testing**: [pytest Documentation](https://docs.pytest.org/)
- **Frontend Testing**: [Jest Documentation](https://jestjs.io/docs)
- **API Testing**: [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- **React Testing**: [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)

---

## ✅ Test Checklist

### **Before Running Tests**
- [ ] Dependencies installed
- [ ] Environment variables set
- [ ] Test data available
- [ ] Database configured (if applicable)

### **After Running Tests**
- [ ] All tests pass
- [ ] Coverage targets met
- [ ] Performance acceptable
- [ ] No flaky tests

### **Before Deployment**
- [ ] Full test suite passes
- [ ] Integration tests pass
- [ ] Performance tests pass
- [ ] Security tests pass

---

This testing guide ensures comprehensive coverage of the Outscaled.GG platform, providing confidence in code quality and reliability! 🚀 