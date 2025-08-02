#!/usr/bin/env python3
"""
Simple Confidence Test Script
Run this to verify the confidence calculation fix is working
"""

import requests
import json
import time

def test_confidence_fix():
    """Test the confidence calculation fix"""
    
    print("🧪 CONFIDENCE CALCULATION TEST")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "name": "Faker - High Gap (OVER)",
            "request": {
                "player_names": ["Faker"],
                "prop_type": "kills",
                "prop_value": 1.0,
                "map_range": [1, 2],
                "opponent": "Gen.G",
                "tournament": "LCK",
                "team": "T1",
                "match_date": "2024-08-01T12:00",
                "position_roles": ["MID"],
                "strict_mode": False
            }
        },
        {
            "name": "Faker - Low Gap (OVER)",
            "request": {
                "player_names": ["Faker"],
                "prop_type": "kills",
                "prop_value": 2.5,
                "map_range": [1, 2],
                "opponent": "Gen.G",
                "tournament": "LCK",
                "team": "T1",
                "match_date": "2024-08-01T12:00",
                "position_roles": ["MID"],
                "strict_mode": False
            }
        },
        {
            "name": "Faker - UNDER Prediction",
            "request": {
                "player_names": ["Faker"],
                "prop_type": "kills",
                "prop_value": 4.0,
                "map_range": [1, 2],
                "opponent": "Gen.G",
                "tournament": "LCK",
                "team": "T1",
                "match_date": "2024-08-01T12:00",
                "position_roles": ["MID"],
                "strict_mode": False
            }
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📊 Test {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            # Make API call
            response = requests.post(
                "http://localhost:8000/predict",
                json=test_case['request'],
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract key data
                expected_stat = result.get('expected_stat', 0)
                top_confidence = result.get('confidence', 0)
                prediction = result.get('prediction', 'UNKNOWN')
                prop_value = test_case['request']['prop_value']
                
                # Find curve confidence for input prop
                curve_confidence = None
                prediction_curve = result.get('prediction_curve', [])
                
                for point in prediction_curve:
                    if point.get('is_input_prop'):
                        curve_confidence = point.get('confidence', 0)
                        break
                
                gap = abs(expected_stat - prop_value)
                
                print(f"  Expected Stat: {expected_stat}")
                print(f"  Prop Value: {prop_value}")
                print(f"  Gap: {gap:.2f}")
                print(f"  Prediction: {prediction}")
                print(f"  Top-Level Confidence: {top_confidence}%")
                print(f"  Curve Confidence: {curve_confidence}%")
                
                # Check consistency
                if curve_confidence is not None:
                    match = abs(top_confidence - curve_confidence) < 0.1
                    print(f"  Consistency: {'✅ PASS' if match else '❌ FAIL'}")
                    
                    if not match:
                        print(f"    ⚠️  Mismatch: {abs(top_confidence - curve_confidence):.1f}% difference")
                else:
                    print(f"  Consistency: ❌ FAIL (No curve data)")
                    match = False
                
                results.append({
                    'test': test_case['name'],
                    'success': True,
                    'match': match,
                    'gap': gap,
                    'top_confidence': top_confidence,
                    'curve_confidence': curve_confidence
                })
                
            else:
                print(f"  ❌ API Error: {response.status_code}")
                results.append({
                    'test': test_case['name'],
                    'success': False,
                    'error': f"API Error: {response.status_code}"
                })
                
        except Exception as e:
            print(f"  ❌ Request Error: {str(e)}")
            results.append({
                'test': test_case['name'],
                'success': False,
                'error': f"Request Error: {str(e)}"
            })
        
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    successful_tests = [r for r in results if r.get('success', False)]
    matching_tests = [r for r in successful_tests if r.get('match', False)]
    
    print(f"Total Tests: {len(results)}")
    print(f"Successful Tests: {len(successful_tests)}")
    print(f"Consistent Confidence: {len(matching_tests)}")
    print(f"Success Rate: {len(successful_tests)/len(results)*100:.1f}%")
    print(f"Consistency Rate: {len(matching_tests)/len(successful_tests)*100:.1f}%" if successful_tests else "N/A")
    
    print("\n📊 Results:")
    for result in results:
        if result.get('success', False):
            status = "✅ PASS" if result.get('match', False) else "❌ FAIL"
            print(f"  {result['test']}: {status}")
        else:
            print(f"  {result['test']}: ❌ ERROR")
    
    # Final verdict
    if len(successful_tests) == len(results) and len(matching_tests) == len(successful_tests):
        print("\n🎉 ALL TESTS PASSED! ✅")
        print("Confidence calculation fix is working correctly.")
    else:
        print("\n⚠️  SOME TESTS FAILED! ❌")
        print("Issues detected in confidence calculation.")

def quick_test():
    """Quick single test for immediate verification"""
    
    print("⚡ QUICK CONFIDENCE TEST")
    print("=" * 40)
    
    request_data = {
        "player_names": ["Faker"],
        "prop_type": "kills",
        "prop_value": 1.0,
        "map_range": [1, 2],
        "opponent": "Gen.G",
        "tournament": "LCK",
        "team": "T1",
        "match_date": "2024-08-01T12:00",
        "position_roles": ["MID"],
        "strict_mode": False
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/predict",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            expected_stat = result.get('expected_stat', 0)
            top_confidence = result.get('confidence', 0)
            prop_value = request_data['prop_value']
            gap = abs(expected_stat - prop_value)
            
            # Find curve confidence
            curve_confidence = None
            prediction_curve = result.get('prediction_curve', [])
            
            for point in prediction_curve:
                if point.get('is_input_prop'):
                    curve_confidence = point.get('confidence', 0)
                    break
            
            print(f"Expected Stat: {expected_stat}")
            print(f"Prop Value: {prop_value}")
            print(f"Gap: {gap:.2f}")
            print(f"Top-Level Confidence: {top_confidence}%")
            print(f"Curve Confidence: {curve_confidence}%")
            
            if curve_confidence is not None:
                match = abs(top_confidence - curve_confidence) < 0.1
                print(f"Consistency: {'✅ PASS' if match else '❌ FAIL'}")
                
                if match:
                    print("\n🎉 CONFIDENCE FIX WORKING! ✅")
                else:
                    print("\n⚠️  CONFIDENCE MISMATCH DETECTED! ❌")
            else:
                print("❌ No curve data found")
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request Error: {str(e)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_test()
    else:
        test_confidence_fix()
        
    print("\n💡 Usage:")
    print("  python run_confidence_tests.py          # Run full test suite")
    print("  python run_confidence_tests.py quick    # Run quick single test") 