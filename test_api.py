"""
API Testing Script
Run this after starting the Flask application to test all endpoints
"""

import requests
import json
import time

BASE_URL = 'http://localhost:5000'

def test_feature_info():
    """Test feature info endpoint"""
    print("\n" + "="*60)
    print("Testing GET /api/feature-info")
    print("="*60)

    try:
        response = requests.get(f'{BASE_URL}/api/feature-info')
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Features loaded: {len(data)} features")
            for feature, values in list(data.items())[:3]:
                print(f"  - {feature}: {values if isinstance(values, str) else f'{len(values)} values'}")
            return True
        else:
            print(f"✗ Failed: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_single_prediction():
    """Test single prediction endpoint"""
    print("\n" + "="*60)
    print("Testing POST /api/predict")
    print("="*60)

    test_data = {
        'Gender': 'Boy',
        'Age': '21-25',
        'Education Level': 'University',
        'Institution Type': 'Government',
        'IT Student': 'Yes',
        'Location': 'Yes',
        'Load-shedding': 'Low',
        'Financial Condition': 'Rich',
        'Internet Type': 'Wifi',
        'Network Type': '4G',
        'Class Duration': '1-3',
        'Self Lms': 'Yes',
        'Device': 'Computer'
    }

    try:
        print("Sending prediction request...")
        response = requests.post(
            f'{BASE_URL}/api/predict',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ Prediction successful!")
            print(f"  - Predicted Level: {result['prediction']}")
            print(f"  - Confidence: {result['confidence']}%")
            print(f"  - Probabilities:")
            for level, prob in result['probabilities'].items():
                print(f"    • {level}: {prob}%")
            return True
        else:
            print(f"✗ Failed: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_metrics():
    """Test metrics endpoint"""
    print("\n" + "="*60)
    print("Testing GET /api/metrics")
    print("="*60)

    try:
        response = requests.get(f'{BASE_URL}/api/metrics')
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            metrics = response.json()
            print(f"\n✓ Metrics retrieved!")
            print(f"  - Accuracy: {metrics['accuracy']}%")
            print(f"  - Precision: {metrics['precision']}%")
            print(f"  - Recall: {metrics['recall']}%")
            print(f"  - F1-Score: {metrics['f1_score']}%")
            print(f"  - Train samples: {metrics['train_samples']}")
            print(f"  - Test samples: {metrics['test_samples']}")
            return True
        else:
            print(f"✗ Failed: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_invalid_prediction():
    """Test prediction with invalid data"""
    print("\n" + "="*60)
    print("Testing POST /api/predict (Invalid Data)")
    print("="*60)

    invalid_data = {
        'Gender': 'Invalid',
        'Age': '21-25'
    }

    try:
        print("Sending invalid prediction request...")
        response = requests.post(
            f'{BASE_URL}/api/predict',
            json=invalid_data,
            headers={'Content-Type': 'application/json'}
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 400:
            print(f"✓ Correctly rejected invalid data")
            print(f"  Error message: {response.json().get('error', 'N/A')}")
            return True
        else:
            print(f"⚠ Unexpected response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_home_page():
    """Test home page loads"""
    print("\n" + "="*60)
    print("Testing GET / (Home Page)")
    print("="*60)

    try:
        response = requests.get(BASE_URL)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            content = response.text
            if 'Student Adaptability' in content:
                print("✓ Home page loaded successfully")
                return True
            else:
                print("⚠ Page loaded but content unexpected")
                return False
        else:
            print(f"✗ Failed to load home page")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def main():
    print("="*60)
    print("Student Adaptability API Test Suite")
    print("="*60)
    print(f"\nTesting API at: {BASE_URL}")
    print("Make sure the Flask application is running!")
    print("\nWaiting 2 seconds before starting tests...")
    time.sleep(2)

    tests = [
        ("Home Page", test_home_page),
        ("Feature Info", test_feature_info),
        ("Single Prediction", test_single_prediction),
        ("Invalid Data Handling", test_invalid_prediction),
        ("Metrics", test_metrics),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            time.sleep(0.5)
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))

    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All API tests passed!")
        print("\nThe application is fully functional and ready to use.")
    else:
        print("\n⚠ Some tests failed.")
        print("Make sure the Flask application is running on port 5000.")

if __name__ == '__main__':
    main()
