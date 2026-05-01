import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from app import create_app


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


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.app = create_app(
            {
                "TESTING": True,
                "MODEL_PATH": root / "models" / "adaptability_pipeline.joblib",
                "METRICS_PATH": root / "models" / "metrics.json",
                "DATASET_PATH": root / "data" / "students_adaptability_level_online_education.csv",
                "BATCH_MAX_ROWS": 50,
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_health_endpoint(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("model_available", payload)

    def test_feature_info_endpoint(self):
        response = self.client.get("/api/feature-info")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload["features"]), 13)
        self.assertEqual(payload["features"][0]["name"], "Gender")
        self.assertIn("Boy", payload["features"][0]["options"])

    def test_prediction_endpoint(self):
        response = self.client.post("/api/predict", json=VALID_STUDENT)

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "success")
        self.assertIn(payload["prediction"], {"Low", "Moderate", "High"})
        self.assertGreaterEqual(payload["confidence"], 0)
        self.assertLessEqual(payload["confidence"], 100)
        self.assertIn("probabilities", payload)

    def test_prediction_validation_error(self):
        invalid_student = {**VALID_STUDENT, "Network Type": "5G"}
        response = self.client.post("/api/predict", json=invalid_student)

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload["status"], "error")
        self.assertIn("validation", payload["error"].lower())

    def test_batch_prediction_endpoint(self):
        csv_content = (
            "Gender,Age,Education Level,Institution Type,IT Student,Location,"
            "Load-shedding,Financial Condition,Internet Type,Network Type,"
            "Class Duration,Self Lms,Device\n"
            "Boy,21-25,University,Government,Yes,Yes,Low,Mid,Wifi,4G,1-3,Yes,Computer\n"
        )
        response = self.client.post(
            "/api/predict-batch",
            data={"file": (BytesIO(csv_content.encode("utf-8")), "students.csv")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")
        self.assertIn("Predicted Adaptivity Level", response.get_data(as_text=True))

    def test_pdf_export_endpoint(self):
        prediction_response = self.client.post("/api/predict", json=VALID_STUDENT)
        prediction_payload = prediction_response.get_json()

        response = self.client.post(
            "/api/export-pdf",
            json={
                "student_data": VALID_STUDENT,
                "prediction_result": prediction_payload,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertTrue(response.get_data().startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
