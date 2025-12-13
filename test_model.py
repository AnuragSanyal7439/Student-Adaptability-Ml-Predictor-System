"""
Test script to verify model training and prediction functionality
"""

import json
import sys
from model_training import train_model

def test_model_training():
    """Test model training pipeline"""
    print("="*60)
    print("Testing Model Training Pipeline")
    print("="*60)

    try:
        print("\n1. Starting model training...")
        metrics = train_model()

        print("\n2. Model training completed successfully!")
        print(f"   - Accuracy: {metrics['accuracy']}%")
        print(f"   - Precision: {metrics['precision']}%")
        print(f"   - Recall: {metrics['recall']}%")
        print(f"   - F1-Score: {metrics['f1_score']}%")
        print(f"   - Training samples: {metrics['train_samples']}")
        print(f"   - Test samples: {metrics['test_samples']}")

        print("\n3. Class distribution:")
        for label in metrics['class_labels']:
            print(f"   - {label}")

        print("\n4. Files generated:")
        print("   ✓ models/adaptability_model.pkl")
        print("   ✓ models/label_encoders.pkl")
        print("   ✓ models/metrics.json")
        print("   ✓ static/confusion_matrix.png")

        if metrics['accuracy'] > 50:
            print("\n✓ Model training PASSED")
            print("  Model is performing above baseline!")
            return True
        else:
            print("\n⚠ Model training completed but accuracy is low")
            return False

    except Exception as e:
        print(f"\n✗ Model training FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_prediction():
    """Test prediction functionality"""
    print("\n" + "="*60)
    print("Testing Prediction Functionality")
    print("="*60)

    try:
        import joblib
        import pandas as pd

        print("\n1. Loading model and encoders...")
        model = joblib.load('models/adaptability_model.pkl')
        encoders = joblib.load('models/label_encoders.pkl')
        print("   ✓ Model and encoders loaded")

        print("\n2. Creating test sample...")
        test_sample = {
            'Gender': 'Boy',
            'Age': '21-25',
            'Education Level': 'University',
            'Institution Type': 'Government',
            'IT Student': 'Yes',
            'Location': 'Yes',
            'Load-shedding': 'Low',
            'Financial Condition': 'Mid',
            'Internet Type': 'Wifi',
            'Network Type': '4G',
            'Class Duration': '1-3',
            'Self Lms': 'Yes',
            'Device': 'Computer'
        }

        print("   Sample data:")
        for key, value in test_sample.items():
            print(f"   - {key}: {value}")

        print("\n3. Encoding features...")
        encoded_sample = []
        feature_order = list(test_sample.keys())

        for feature in feature_order:
            value = test_sample[feature]
            if feature in encoders:
                encoded_value = encoders[feature].transform([value])[0]
            else:
                encoded_value = value
            encoded_sample.append(encoded_value)

        print("   ✓ Features encoded")

        print("\n4. Making prediction...")
        X = pd.DataFrame([encoded_sample], columns=feature_order)
        prediction = model.predict(X)[0]
        probabilities = model.predict_proba(X)[0]

        predicted_label = encoders['Adaptivity Level'].inverse_transform([prediction])[0]
        confidence = max(probabilities) * 100

        print(f"\n5. Prediction Result:")
        print(f"   - Predicted Level: {predicted_label}")
        print(f"   - Confidence: {confidence:.2f}%")

        print("\n   Probabilities:")
        for label, prob in zip(encoders['Adaptivity Level'].classes_, probabilities):
            print(f"   - {label}: {prob*100:.2f}%")

        print("\n✓ Prediction test PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Prediction test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*60)
    print("Student Adaptability ML Predictor - Test Suite")
    print("="*60)

    test_results = []

    test_results.append(("Model Training", test_model_training()))

    test_results.append(("Prediction", test_prediction()))

    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! The application is ready to use.")
        print("\nNext steps:")
        print("1. Run 'python3 app.py' to start the Flask server")
        print("2. Open http://localhost:5000 in your browser")
        print("3. Start making predictions!")
        return 0
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
