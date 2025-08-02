# Confidence Calculation Testing Guide

This guide explains how to test the confidence calculation fix that was implemented to resolve the mismatch between top-level confidence and prediction curve confidence.

## 🚀 Quick Start

### Prerequisites
1. Make sure the backend is running (Docker or local)
2. Ensure the API is accessible at `http://localhost:8000`

### Running Tests

#### Option 1: Quick Test (Recommended for first-time verification)
```bash
cd backend
python run_confidence_tests.py quick
```

This runs a single test to quickly verify the fix is working.

#### Option 2: Full Test Suite
```bash
cd backend
python run_confidence_tests.py
```

This runs multiple test cases to thoroughly verify the fix.

## 📊 What the Tests Check

The tests verify that:

1. **Consistency**: Top-level confidence matches prediction curve confidence
2. **Logic**: Confidence varies appropriately with gap size
3. **Edge Cases**: System handles various prop values correctly
4. **Real Data**: All tests use actual player data (no mocks)

## ✅ Expected Results

When the fix is working correctly, you should see:

```
🎉 ALL TESTS PASSED! ✅
Confidence calculation fix is working correctly.
```

### Sample Output
```
📊 Test 1: Faker - High Gap (OVER)
  Expected Stat: 2.9
  Prop Value: 1.0
  Gap: 1.90
  Prediction: OVER
  Top-Level Confidence: 66.3%
  Curve Confidence: 66.3%
  Consistency: ✅ PASS
```

## 🔧 Troubleshooting

### If tests fail:

1. **Check if backend is running**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Restart Docker containers**:
   ```bash
   cd ..
   docker-compose down
   docker-compose up -d
   ```

3. **Check Docker logs**:
   ```bash
   docker logs outscaled2-backend-1
   ```

### Common Issues

- **Connection refused**: Backend not running
- **Timeout errors**: Backend taking too long to respond
- **Confidence mismatch**: Old code still running (restart needed)

## 🧪 Manual Testing

You can also test manually using curl:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "player_names": ["Faker"],
    "prop_type": "kills",
    "prop_value": 1.0,
    "map_range": [1, 2],
    "opponent": "Gen.G",
    "tournament": "LCK",
    "team": "T1",
    "match_date": "2024-08-01T12:00",
    "position_roles": ["MID"],
    "strict_mode": false
  }'
```

## 📈 Understanding the Fix

The confidence calculation fix ensures that:

1. **Dynamic Gap-Based Adjustment**: Confidence is calculated based on the gap between expected_stat and prop_value
2. **Consistent Logic**: Both top-level and curve confidence use the same calculation
3. **Logical Scaling**: Larger gaps result in higher confidence, smaller gaps in lower confidence

### Before vs After

**Before (Broken)**:
- Top-level confidence: 23%
- Curve confidence: 73%
- **Mismatch**: 50% difference

**After (Fixed)**:
- Top-level confidence: 66.3%
- Curve confidence: 66.3%
- **Match**: ✅ Perfect consistency

## 🎯 Production Readiness

The fix is production-ready when:
- ✅ All tests pass
- ✅ No confidence mismatches
- ✅ Real data validation complete
- ✅ Edge cases handled properly 