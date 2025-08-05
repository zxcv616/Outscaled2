# Feature Validation Test Suite

This comprehensive test suite validates that feature extraction produces consistent results between training and prediction phases after ML pipeline fixes.

## 🎯 Purpose

The ML pipeline had critical issues with feature extraction consistency:
- Training and prediction paths calculated features differently
- Position filtering was inconsistent or broken  
- Edge cases (missing data, zero values) caused failures
- Combined vs average statistics logic was incorrect for betting terminology

These tests ensure all issues are resolved and the pipeline is consistent.

## 📋 Test Suites

### 1. Core Feature Validation (`test_feature_validation.py`)
- **Training vs Prediction Consistency**: Ensures identical feature extraction
- **Feature Vector Ordering**: Validates consistent feature order across calls
- **Edge Case Handling**: Tests missing data, zero values, extreme values
- **Model Integration**: Verifies features work correctly with predictions
- **Determinism**: Ensures same input always produces same output

### 2. Position Filtering Validation (`test_position_filtering_validation.py`)
- **Alias Mapping**: Tests bot→adc, jng→jungle, sup→support mappings
- **Case Insensitivity**: Validates MID, mid, Mid all work consistently  
- **Feature Impact**: Ensures position filtering affects averages correctly
- **Training/Prediction Consistency**: Same filtering logic in both paths
- **Edge Cases**: Missing positions, unknown roles, empty data
- **Position Factor Neutrality**: Confirms no role-based stat adjustments

### 3. Betting Logic Validation (`test_betting_logic_validation.py`)
- **Combined vs Average**: Tests proper betting terminology (Maps 1-2 = total, not average)
- **Series-Based Features**: Validates grouping by match_series for combined stats
- **Historical Analysis**: Ensures combined performance calculation is correct
- **Prop Generation**: Tests realistic betting prop creation using combined logic
- **Training Data**: Validates series-based outcomes for model training
- **Backward Compatibility**: Ensures average-based features still work

## 🚀 Usage

### Run All Validation Tests
```bash
cd backend
python run_feature_validation_tests.py
```

### Run with Verbose Output
```bash
python run_feature_validation_tests.py --verbose
```

### Run Specific Test Suite
```bash
python run_feature_validation_tests.py --suite test_feature_validation
python run_feature_validation_tests.py --suite test_position_filtering_validation
```

### Run Individual Test
```bash
python run_feature_validation_tests.py --specific-test test_feature_validation.TestFeatureExtractionValidation.test_training_vs_prediction_feature_consistency
```

### Run with Standard unittest
```bash
python -m pytest tests/test_feature_validation.py -v
python -m pytest tests/test_position_filtering_validation.py -v
python -m pytest tests/test_betting_logic_validation.py -v
```

## 📊 Expected Results

### Before Fixes (❌ Expected Failures)
- Many tests will FAIL due to inconsistent feature extraction
- Position filtering may be broken or inconsistent
- Combined statistics logic missing or incorrect
- Training and prediction paths produce different results

### After Fixes (✅ Expected Passes)  
- All tests should PASS indicating consistent pipeline behavior
- Position filtering works correctly across all scenarios
- Combined statistics properly implement betting terminology
- Feature extraction is deterministic and reliable

## 🔍 Test Categories

### Consistency Tests
- Feature extraction produces identical results between training/prediction
- Position filtering applies same logic in both paths
- Feature vectors maintain consistent ordering
- Multiple calls with same input produce same output

### Edge Case Tests  
- Missing data handled gracefully (NaN, None, empty)
- Zero values don't cause failures or incorrect calculations
- Extreme statistical values processed correctly
- Unknown positions handled without errors

### Betting Logic Tests
- Combined statistics calculated correctly (series totals, not averages)
- Historical analysis uses proper combined methodology  
- Prop generation reflects betting market logic
- Expected stat calculation uses combined approach

### Integration Tests
- Features work correctly with model predictions
- Full pipeline (data → features → prediction) functions properly
- Backward compatibility maintained with existing code
- Error handling prevents crashes in production

## 🧪 Test Data

Tests use carefully crafted datasets that expose common issues:

- **Series-based data**: Clear separation between individual maps and series
- **Position variants**: All position names, aliases, and edge cases  
- **Edge cases**: Missing values, zeros, extreme outliers
- **Realistic scenarios**: Data that reflects actual League of Legends statistics

## 📈 Success Metrics

### 100% Pass Rate
- **Feature Consistency**: Training and prediction extract identical features
- **Position Filtering**: Correctly filters and affects feature calculation  
- **Edge Case Handling**: No crashes or incorrect values with problematic data
- **Betting Logic**: Combined statistics properly implemented throughout

### Performance Indicators
- **Determinism**: Same input always produces same feature output
- **Correctness**: Feature values match expected calculations
- **Completeness**: All required features present and valid
- **Robustness**: Handles edge cases without errors

## 🔧 Troubleshooting

### Common Issues Before Fixes

1. **Feature Inconsistency**
   ```
   AssertionError: Feature avg_kills inconsistent: training=4.0, prediction=3.5
   ```
   - Different calculation methods in training vs prediction paths

2. **Position Filtering Failures**
   ```
   AssertionError: Position filtering should affect average kills
   ```
   - Position filtering not implemented or not working correctly

3. **Edge Case Crashes**
   ```
   ValueError: cannot convert float NaN to integer
   ```
   - Missing data not handled properly in feature extraction

4. **Combined Logic Missing**
   ```
   ⚠️ combined_kills feature not found - betting logic fix not implemented
   ```
   - Betting terminology fixes not implemented

### Debug Steps

1. **Run with verbose output** to see detailed test results
2. **Check specific failing tests** for exact error messages  
3. **Review feature extraction code** in `prediction_model.py` and `data_processor.py`
4. **Verify data processing logic** handles edge cases correctly
5. **Confirm position filtering implementation** in data processor

## 📝 Validation Checklist

After running tests, confirm:

- [ ] All feature validation tests pass (consistency, ordering, edge cases)
- [ ] All position filtering tests pass (aliases, case sensitivity, impact)  
- [ ] All betting logic tests pass (combined stats, series-based features)
- [ ] Integration tests demonstrate full pipeline functionality
- [ ] Edge cases handled gracefully without crashes
- [ ] Backward compatibility maintained with existing features

## 🎉 Success Confirmation

When all tests pass:
- **ML pipeline is consistent** between training and prediction
- **Position filtering works correctly** and affects features properly
- **Betting terminology is implemented** with combined statistics logic  
- **Edge cases are handled** without causing failures
- **System is ready for production** with validated feature extraction

This comprehensive validation ensures the ML pipeline fixes are complete and the system is robust for production use.