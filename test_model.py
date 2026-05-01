import tempfile
import unittest
from pathlib import Path

import joblib
import pandas as pd

import model_training


VALID_STUDENT = {
    "Gender": "Boy",
    "Age": "21-25",
    "Education Level": "University",
    "Institution Type": "Government",
    "IT Student": "Yes",
    "Location": "Yes",
    "Load-shedding": "Low",
    "Financial Condition": "Mid",
    "Internet Type": "Wifi",
    "Network Type": "4G",
    "Class Duration": "1-3",
    "Self Lms": "Yes",
    "Device": "Computer",
}


class ModelTrainingTestCase(unittest.TestCase):
    def test_model_training_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dataset_path = root / "data" / "students_adaptability_level_online_education.csv"
            model_path = root / "models" / "adaptability_pipeline.joblib"
            metrics_path = root / "models" / "metrics.json"

            metrics = model_training.train_model(
                dataset_path=dataset_path,
                model_path=model_path,
                metrics_path=metrics_path,
            )

            self.assertTrue(dataset_path.exists())
            self.assertTrue(model_path.exists())
            self.assertTrue(metrics_path.exists())
            self.assertIn(metrics["selected_model_name"], metrics["model_comparison"])
            self.assertGreaterEqual(metrics["accuracy"], 0)
            self.assertLessEqual(metrics["accuracy"], 100)
            self.assertGreater(metrics["train_samples"], 0)
            self.assertGreater(metrics["test_samples"], 0)
            self.assertEqual(metrics["feature_columns"], model_training.FEATURE_COLUMNS)

            bundle = joblib.load(model_path)
            self.assertIn("pipeline", bundle)
            self.assertEqual(bundle["feature_columns"], model_training.FEATURE_COLUMNS)

            sample = pd.DataFrame([VALID_STUDENT], columns=model_training.FEATURE_COLUMNS)
            prediction = bundle["pipeline"].predict(sample)[0]
            probabilities = bundle["pipeline"].predict_proba(sample)[0]

            self.assertIn(prediction, model_training.TARGET_LABELS)
            self.assertAlmostEqual(float(probabilities.sum()), 1.0, places=5)


if __name__ == "__main__":
    unittest.main()
