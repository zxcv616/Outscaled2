# Test Fixes TODO

## Current Issues ❌
- Tests timing out due to database initialization in startup event
- Authentication system causing import issues in test environment
- Missing sample_details field in API responses
- Database models need proper test configuration

## Completed Fixes ✅
- [x] Installed authentication dependencies (python-jose, passlib, sqlalchemy)
- [x] Fixed SQLAlchemy deprecation warnings
- [x] Fixed Pydantic config deprecation warnings
- [x] Created test_api_fixed.py with mocked dependencies

## TODO - Test Environment Setup
- [ ] Create test-specific configuration that skips database startup
- [ ] Mock authentication dependencies in test environment
- [ ] Set up in-memory SQLite database for tests
- [ ] Create test fixtures for user authentication
- [ ] Add test database cleanup between tests

## TODO - Fix Specific Test Failures

### 1. API Endpoint Tests
- [ ] Fix sample_details field missing in prediction responses
- [ ] Mock data processor and prediction model properly
- [ ] Add proper error handling for database-dependent tests
- [ ] Create test data factories

### 2. Data Processor Tests
- [ ] Fix engineer_features test with empty data handling
- [ ] Update test expectations to match new authentication features
- [ ] Add tests for new data ingestion system
- [ ] Test tiered data filtering with real scenarios

### 3. Authentication Tests
- [ ] Create comprehensive authentication test suite
- [ ] Test JWT token generation and validation
- [ ] Test rate limiting functionality
- [ ] Test subscription tier enforcement
- [ ] Test API key management

## TODO - Test Infrastructure
- [ ] Set up pytest fixtures for common test data
- [ ] Create mock factories for complex objects
- [ ] Add test coverage reporting
- [ ] Set up continuous integration test pipeline
- [ ] Add performance testing suite

## Quick Fixes Available

### 1. Database Startup Issue
```python
# In test files, mock the startup event
@pytest.fixture(autouse=True)
def mock_startup():
    with patch('app.main.init_db'):
        yield
```

### 2. Authentication Mocking
```python
# Mock authentication dependencies
@patch('app.auth.dependencies.get_current_user_optional')
@patch('app.database.get_db')
def test_with_auth(mock_db, mock_user):
    # Test implementation
    pass
```

### 3. Response Model Fix
Add sample_details to prediction response:
```python
# In prediction endpoint
prediction_result['sample_details'] = sample_details or {}
```

## Test Results Status
- **Current**: 5 failing tests out of 50 total
- **Main Issues**: Database timeout, missing fields, import errors
- **Target**: 100% passing tests with proper mocking

## Running Tests Safely

For immediate testing without timeouts:
```bash
# Run specific test modules
python -m pytest tests/test_prediction_model.py -v
python -m pytest tests/test_advanced_features.py -v

# Run with shorter timeout
python -m pytest tests/ --timeout=30
```