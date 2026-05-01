"""
Flask API for the Student Adaptability ML Predictor.

Run with:
    python app.py
"""

from __future__ import annotations

import html
import json
import logging
import os
import threading
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

import model_training

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
FEATURE_ORDER = model_training.FEATURE_COLUMNS
TARGET_COLUMN = model_training.TARGET_COLUMN


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    return Path(value).expanduser().resolve() if value else default


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config.update(
        MODEL_PATH=_env_path("MODEL_PATH", model_training.MODEL_PATH),
        METRICS_PATH=_env_path("METRICS_PATH", model_training.METRICS_PATH),
        DATASET_PATH=_env_path("DATASET_PATH", model_training.DATASET_PATH),
        FRONTEND_DIST=_env_path("FRONTEND_DIST", BASE_DIR / "dist"),
        MAX_CONTENT_LENGTH=int(os.getenv("MAX_UPLOAD_MB", "2")) * 1024 * 1024,
        BATCH_MAX_ROWS=int(os.getenv("BATCH_MAX_ROWS", "1000")),
    )
    if test_config:
        app.config.update(test_config)

    cors_origins = os.getenv("CORS_ORIGINS", "*")
    CORS(app, resources={r"/api/*": {"origins": cors_origins.split(",")}})

    model_lock = threading.Lock()
    model_state: dict[str, Any] = {"bundle": None}

    def error_response(
        message: str,
        status_code: int = 400,
        details: Any | None = None,
    ):
        payload: dict[str, Any] = {
            "status": "error",
            "error": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if details is not None:
            payload["details"] = details
        return jsonify(payload), status_code

    def ensure_model_bundle() -> dict[str, Any]:
        if model_state["bundle"] is not None:
            return model_state["bundle"]

        with model_lock:
            if model_state["bundle"] is not None:
                return model_state["bundle"]

            model_path = Path(app.config["MODEL_PATH"])
            if not model_path.exists():
                logger.info("Model not found at %s. Training a new pipeline.", model_path)
                model_training.train_model(
                    dataset_path=Path(app.config["DATASET_PATH"]),
                    model_path=model_path,
                    metrics_path=Path(app.config["METRICS_PATH"]),
                )

            bundle = joblib.load(model_path)
            if not isinstance(bundle, dict) or "pipeline" not in bundle:
                raise RuntimeError("Saved model artifact is invalid. Retrain the model.")

            model_state["bundle"] = bundle
            return bundle

    def get_feature_options() -> dict[str, list[str]]:
        bundle = model_state.get("bundle")
        if bundle and bundle.get("feature_options"):
            return bundle["feature_options"]

        feature_info_path = Path(app.config["METRICS_PATH"]).with_name("feature_info.json")
        if feature_info_path.exists():
            with feature_info_path.open("r", encoding="utf-8") as file:
                return json.load(file)

        return model_training.get_feature_options(Path(app.config["DATASET_PATH"]))

    def validate_student_payload(
        payload: Any,
        feature_options: dict[str, list[str]],
    ) -> tuple[dict[str, str] | None, list[dict[str, Any]]]:
        if not isinstance(payload, dict):
            return None, [{"field": "body", "message": "JSON object is required."}]

        errors: list[dict[str, Any]] = []
        cleaned: dict[str, str] = {}

        for feature in FEATURE_ORDER:
            if feature not in payload:
                errors.append({"field": feature, "message": "This field is required."})
                continue

            value = "" if payload[feature] is None else str(payload[feature]).strip()
            if not value:
                errors.append({"field": feature, "message": "A value is required."})
                continue

            allowed_values = feature_options.get(feature, [])
            if allowed_values and value not in allowed_values:
                errors.append(
                    {
                        "field": feature,
                        "message": f"Invalid value: {value}",
                        "allowed_values": allowed_values,
                    }
                )
                continue

            cleaned[feature] = value

        unknown_fields = sorted(set(payload.keys()) - set(FEATURE_ORDER))
        if unknown_fields:
            errors.append(
                {
                    "field": "body",
                    "message": "Unexpected fields were provided.",
                    "fields": unknown_fields,
                }
            )

        return (None if errors else cleaned), errors

    def build_prediction(cleaned_payload: dict[str, str], bundle: dict[str, Any]) -> dict[str, Any]:
        pipeline = bundle["pipeline"]
        input_frame = pd.DataFrame([cleaned_payload], columns=FEATURE_ORDER)
        prediction = str(pipeline.predict(input_frame)[0])

        probabilities: dict[str, float] = {}
        confidence = 0.0
        if hasattr(pipeline, "predict_proba"):
            probability_values = pipeline.predict_proba(input_frame)[0]
            class_labels = [str(label) for label in getattr(pipeline, "classes_", bundle["class_labels"])]
            probabilities = {
                label: round(float(probability) * 100, 2)
                for label, probability in zip(class_labels, probability_values)
            }
            confidence = round(max(probabilities.values()), 2)

        return {
            "prediction": prediction,
            "confidence": confidence,
            "probabilities": probabilities,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_upload(_: RequestEntityTooLarge):
        return error_response("Uploaded file is too large.", 413)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        if isinstance(error, HTTPException):
            return error_response(error.description, error.code or 500)
        logger.exception("Unhandled server error")
        return error_response("Internal server error.", 500)

    @app.get("/api/health")
    def health():
        model_path = Path(app.config["MODEL_PATH"])
        metrics_path = Path(app.config["METRICS_PATH"])
        return jsonify(
            {
                "status": "ok",
                "service": "Student Adaptability ML Predictor API",
                "model_available": model_path.exists(),
                "model_loaded": model_state["bundle"] is not None,
                "metrics_available": metrics_path.exists(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    @app.get("/api/feature-info")
    def feature_info():
        options = get_feature_options()
        return jsonify(
            {
                "features": [
                    {
                        "name": feature,
                        "type": "categorical",
                        "options": options.get(feature, []),
                    }
                    for feature in FEATURE_ORDER
                ],
                "feature_order": FEATURE_ORDER,
                "target": TARGET_COLUMN,
                "target_options": model_training.TARGET_LABELS,
            }
        )

    @app.post("/api/predict")
    def predict():
        payload = request.get_json(silent=True)
        feature_options = get_feature_options()
        cleaned_payload, errors = validate_student_payload(payload, feature_options)
        if errors:
            return error_response("Prediction input validation failed.", 400, errors)

        bundle = ensure_model_bundle()
        prediction = build_prediction(cleaned_payload or {}, bundle)
        return jsonify({"status": "success", **prediction})

    @app.post("/api/predict-batch")
    def predict_batch():
        if "file" not in request.files:
            return error_response("CSV file is required.", 400)

        uploaded_file = request.files["file"]
        if not uploaded_file.filename:
            return error_response("CSV filename is empty.", 400)
        if not uploaded_file.filename.lower().endswith(".csv"):
            return error_response("Only CSV files are supported.", 400)

        try:
            df = pd.read_csv(uploaded_file)
        except Exception:
            logger.exception("Failed to parse uploaded CSV")
            return error_response("Could not read the uploaded CSV file.", 400)

        if df.empty:
            return error_response("CSV file has no rows.", 400)
        if len(df) > int(app.config["BATCH_MAX_ROWS"]):
            return error_response(
                f"CSV file has too many rows. Maximum allowed is {app.config['BATCH_MAX_ROWS']}.",
                400,
            )

        missing_columns = [feature for feature in FEATURE_ORDER if feature not in df.columns]
        if missing_columns:
            return error_response("CSV is missing required columns.", 400, missing_columns)

        feature_options = get_feature_options()
        validation_errors: list[dict[str, Any]] = []
        cleaned_df = df.copy()

        for feature in FEATURE_ORDER:
            series = df[feature].fillna("").astype(str).str.strip()
            allowed_values = feature_options.get(feature, [])
            invalid_mask = ~series.isin(allowed_values)
            if invalid_mask.any():
                validation_errors.append(
                    {
                        "field": feature,
                        "message": "Column contains invalid values.",
                        "rows": (series[invalid_mask].index + 2).tolist()[:10],
                        "invalid_values": sorted(series[invalid_mask].unique().tolist())[:10],
                        "allowed_values": allowed_values,
                    }
                )
            cleaned_df[feature] = series

        if validation_errors:
            return error_response("Batch CSV validation failed.", 400, validation_errors)

        bundle = ensure_model_bundle()
        pipeline = bundle["pipeline"]
        prediction_frame = cleaned_df[FEATURE_ORDER]
        predictions = pipeline.predict(prediction_frame)
        probabilities = pipeline.predict_proba(prediction_frame)
        class_labels = [str(label) for label in getattr(pipeline, "classes_", bundle["class_labels"])]

        result_df = df.copy()
        result_df["Predicted Adaptivity Level"] = predictions
        result_df["Prediction Confidence (%)"] = [
            round(float(row.max()) * 100, 2) for row in probabilities
        ]
        for index, label in enumerate(class_labels):
            result_df[f"Probability {label} (%)"] = [
                round(float(row[index]) * 100, 2) for row in probabilities
            ]

        output = BytesIO(result_df.to_csv(index=False).encode("utf-8"))
        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"student_adaptability_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )

    @app.get("/api/metrics")
    def metrics():
        metrics_path = Path(app.config["METRICS_PATH"])
        if metrics_path.exists():
            with metrics_path.open("r", encoding="utf-8") as file:
                return jsonify(json.load(file))

        bundle = ensure_model_bundle()
        return jsonify(bundle.get("metrics", {}))

    @app.post("/api/export-pdf")
    def export_pdf():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return error_response("JSON object is required.", 400)

        student_data = payload.get("student_data")
        prediction_result = payload.get("prediction_result")
        if not isinstance(student_data, dict) or not isinstance(prediction_result, dict):
            return error_response(
                "student_data and prediction_result objects are required.",
                400,
            )

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, title="Student Adaptability Report")
        styles = getSampleStyleSheet()
        elements: list[Any] = [
            Paragraph("Student Adaptability Prediction Report", styles["Title"]),
            Spacer(1, 16),
            Paragraph(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                styles["Normal"],
            ),
            Spacer(1, 16),
        ]

        student_rows = [["Feature", "Value"]]
        for feature in FEATURE_ORDER:
            value = html.escape(str(student_data.get(feature, "")))
            student_rows.append([feature, value])

        student_table = Table(student_rows, hAlign="LEFT")
        student_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.extend([student_table, Spacer(1, 18)])

        prediction = html.escape(str(prediction_result.get("prediction", "N/A")))
        confidence = html.escape(str(prediction_result.get("confidence", "N/A")))
        elements.append(Paragraph(f"<b>Predicted Adaptivity Level:</b> {prediction}", styles["Heading2"]))
        elements.append(Paragraph(f"<b>Confidence:</b> {confidence}%", styles["Normal"]))
        elements.append(Spacer(1, 12))

        probabilities = prediction_result.get("probabilities", {})
        if isinstance(probabilities, dict) and probabilities:
            probability_rows = [["Level", "Probability"]]
            for label, probability in probabilities.items():
                probability_rows.append([html.escape(str(label)), f"{html.escape(str(probability))}%"])

            probability_table = Table(probability_rows, hAlign="LEFT")
            probability_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ecfeff")]),
                        ("PADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            elements.append(probability_table)

        doc.build(elements)
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"student_adaptability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        )

    @app.post("/api/retrain")
    def retrain():
        metrics_result = model_training.train_model(
            dataset_path=Path(app.config["DATASET_PATH"]),
            model_path=Path(app.config["MODEL_PATH"]),
            metrics_path=Path(app.config["METRICS_PATH"]),
        )
        with model_lock:
            model_state["bundle"] = joblib.load(Path(app.config["MODEL_PATH"]))

        return jsonify(
            {
                "status": "success",
                "message": "Model retrained successfully.",
                "metrics": metrics_result,
            }
        )

    @app.get("/")
    def root():
        dist_dir = Path(app.config["FRONTEND_DIST"])
        if (dist_dir / "index.html").exists():
            return send_from_directory(dist_dir, "index.html")

        return jsonify(
            {
                "status": "ok",
                "message": "Flask API is running. Start the React frontend with npm run dev.",
                "api_docs": {
                    "health": "/api/health",
                    "feature_info": "/api/feature-info",
                    "predict": "/api/predict",
                    "batch_predict": "/api/predict-batch",
                    "metrics": "/api/metrics",
                },
            }
        )

    @app.get("/assets/<path:filename>")
    def frontend_assets(filename: str):
        dist_assets = Path(app.config["FRONTEND_DIST"]) / "assets"
        return send_from_directory(dist_assets, filename)

    @app.get("/<path:path>")
    def frontend_fallback(path: str):
        if path.startswith("api/"):
            return error_response("API endpoint not found.", 404)

        dist_dir = Path(app.config["FRONTEND_DIST"])
        requested_file = dist_dir / path
        if requested_file.exists() and requested_file.is_file():
            return send_from_directory(dist_dir, path)
        if (dist_dir / "index.html").exists():
            return send_from_directory(dist_dir, "index.html")
        return error_response("Not found.", 404)

    return app


app = create_app()


if __name__ == "__main__":
    model_training.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_training.DATA_DIR.mkdir(parents=True, exist_ok=True)
    model_training.STATIC_DIR.mkdir(parents=True, exist_ok=True)

    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("FLASK_PORT", "5000")))
    debug = _env_bool("FLASK_DEBUG", False)
