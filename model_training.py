"""
Training pipeline for the Student Adaptability ML Predictor.

The saved artifact is a complete scikit-learn Pipeline, so the Flask API can
predict from raw form values without repeating preprocessing logic.
"""

from __future__ import annotations

import json
import logging
from collections import OrderedDict
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
STATIC_DIR = BASE_DIR / "static"

DATASET_PATH = DATA_DIR / "students_adaptability_level_online_education.csv"
MODEL_PATH = MODEL_DIR / "adaptability_pipeline.joblib"
METRICS_PATH = MODEL_DIR / "metrics.json"
FEATURE_INFO_PATH = MODEL_DIR / "feature_info.json"
CONFUSION_MATRIX_PATH = STATIC_DIR / "confusion_matrix.png"

FEATURE_OPTIONS: "OrderedDict[str, list[str]]" = OrderedDict(
    [
        ("Gender", ["Boy", "Girl"]),
        ("Age", ["1-5", "6-10", "11-15", "16-20", "21-25", "26-30"]),
        ("Education Level", ["School", "College", "University"]),
        ("Institution Type", ["Government", "Non Government"]),
        ("IT Student", ["No", "Yes"]),
        ("Location", ["No", "Yes"]),
        ("Load-shedding", ["Low", "High"]),
        ("Financial Condition", ["Poor", "Mid", "Rich"]),
        ("Internet Type", ["Mobile Data", "Wifi"]),
        ("Network Type", ["2G", "3G", "4G"]),
        ("Class Duration", ["0", "1-3", "3-6"]),
        ("Self Lms", ["No", "Yes"]),
        ("Device", ["Mobile", "Tab", "Computer"]),
    ]
)

FEATURE_COLUMNS = list(FEATURE_OPTIONS.keys())
TARGET_COLUMN = "Adaptivity Level"
TARGET_LABELS = ["Low", "Moderate", "High"]


def _ordered_unique(values: pd.Series, known_order: list[str]) -> list[str]:
    """Return dataset values, preserving the expected UI order where possible."""
    seen = [str(value).strip() for value in values.dropna().unique()]
    known = [value for value in known_order if value in seen]
    extras = sorted(value for value in seen if value not in known_order)
    return known + extras


def create_sample_dataset(dataset_path: Path = DATASET_PATH, n_samples: int = 1205) -> pd.DataFrame:
    """
    Create a lightweight sample dataset when the Kaggle CSV is not available.

    The generated labels follow understandable rules so students can explain the
    model behavior during a viva without needing a black-box synthetic process.
    """
    logger.info("Creating sample dataset at %s", dataset_path)
    rng = np.random.default_rng(42)

    data: dict[str, np.ndarray] = {
        feature: rng.choice(options, n_samples) for feature, options in FEATURE_OPTIONS.items()
    }

    score = np.full(n_samples, 0.5)
    score += np.where(data["Financial Condition"] == "Rich", 0.18, 0)
    score += np.where(data["Financial Condition"] == "Poor", -0.20, 0)
    score += np.where(data["Internet Type"] == "Wifi", 0.12, -0.08)
    score += np.where(data["Network Type"] == "4G", 0.12, 0)
    score += np.where(data["Network Type"] == "2G", -0.15, 0)
    score += np.where(data["Load-shedding"] == "Low", 0.10, -0.12)
    score += np.where(data["Device"] == "Computer", 0.12, 0)
    score += np.where(data["Device"] == "Mobile", -0.08, 0)
    score += np.where(data["Self Lms"] == "Yes", 0.10, -0.06)
    score += np.where(data["IT Student"] == "Yes", 0.07, 0)
    score += np.where(data["Class Duration"] == "3-6", 0.08, 0)
    score += rng.normal(0, 0.12, n_samples)

    labels = np.select(
        [score < 0.42, score > 0.72],
        ["Low", "High"],
        default="Moderate",
    )

    df = pd.DataFrame(data)
    df[TARGET_COLUMN] = labels

    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dataset_path, index=False)
    logger.info("Sample dataset created with %s records", len(df))
    return df


def load_dataset(dataset_path: Path = DATASET_PATH) -> pd.DataFrame:
    """Load, normalize, and validate the training dataset."""
    dataset_path = Path(dataset_path)
    if not dataset_path.exists():
        df = create_sample_dataset(dataset_path)
    else:
        df = pd.read_csv(dataset_path)

    df.columns = [str(column).strip() for column in df.columns]
    required_columns = FEATURE_COLUMNS + [TARGET_COLUMN]
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {', '.join(missing_columns)}")

    df = df[required_columns].copy()
    before_drop = len(df)
    df = df.dropna()
    logger.info("Loaded dataset %s with shape %s", dataset_path, df.shape)
    if before_drop != len(df):
        logger.info("Dropped %s rows containing missing values", before_drop - len(df))

    for column in required_columns:
        df[column] = df[column].astype(str).str.strip()

    if df.empty:
        raise ValueError("Dataset has no usable rows after cleaning.")

    return df


def get_feature_options(dataset_path: Path = DATASET_PATH) -> dict[str, list[str]]:
    """Return valid options for every feature, derived from the dataset."""
    df = load_dataset(dataset_path)
    return {
        feature: _ordered_unique(df[feature], FEATURE_OPTIONS[feature])
        for feature in FEATURE_COLUMNS
    }


def _build_pipeline(estimator: Any) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                FEATURE_COLUMNS,
            )
        ],
        remainder="drop",
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", estimator),
        ]
    )


def _candidate_models() -> dict[str, Any]:
    return {
        "GaussianNB": GaussianNB(),
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            class_weight="balanced",
            n_jobs=-1,
        ),
        "GradientBoostingClassifier": GradientBoostingClassifier(random_state=42),
    }


def _round_percent(value: float) -> float:
    return round(float(value) * 100, 2)


def _model_metrics(y_true: pd.Series, y_pred: np.ndarray, class_labels: list[str]) -> dict[str, Any]:
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0,
    )
    return {
        "accuracy": _round_percent(accuracy_score(y_true, y_pred)),
        "precision": _round_percent(precision),
        "recall": _round_percent(recall),
        "f1_score": _round_percent(f1),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=class_labels).tolist(),
        "classification_report": classification_report(
            y_true,
            y_pred,
            labels=class_labels,
            target_names=class_labels,
            output_dict=True,
            zero_division=0,
        ),
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)


def generate_visualizations(
    confusion: list[list[int]],
    class_labels: list[str],
    accuracy_percent: float,
    output_path: Path = CONFUSION_MATRIX_PATH,
) -> None:
    """Generate a confusion matrix image used by the metrics UI."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import seaborn as sns
    except Exception as error:
        logger.warning("Skipping confusion matrix image generation: %s", error)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 6))
    sns.heatmap(
        confusion,
        annot=True,
        fmt="d",
        cmap="YlGnBu",
        xticklabels=class_labels,
        yticklabels=class_labels,
        cbar_kws={"label": "Count"},
    )
    plt.title(f"Confusion Matrix (Accuracy: {accuracy_percent:.2f}%)", fontsize=14)
    plt.ylabel("Actual")
    plt.xlabel("Predicted")
    plt.tight_layout()
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close()
    logger.info("Saved confusion matrix to %s", output_path)


def train_model(
    dataset_path: Path = DATASET_PATH,
    model_path: Path = MODEL_PATH,
    metrics_path: Path = METRICS_PATH,
    generate_plot: bool = False,
) -> dict[str, Any]:
    """
    Train several beginner-friendly classifiers and save the best pipeline.

    The best model is chosen primarily by weighted F1-score and secondarily by
    accuracy, which is more reliable than accuracy alone when classes are uneven.
    """
    logger.info("Starting training pipeline")
    df = load_dataset(dataset_path)
    feature_options = get_feature_options(dataset_path)

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    class_labels = [label for label in TARGET_LABELS if label in set(y)]
    class_labels += sorted(label for label in set(y) if label not in class_labels)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    comparison: dict[str, dict[str, float]] = {}
    best_name = ""
    best_pipeline: Pipeline | None = None
    best_metrics: dict[str, Any] | None = None
    best_sort_key = (-1.0, -1.0)

    for model_name, estimator in _candidate_models().items():
        pipeline = _build_pipeline(estimator)
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)
        current_metrics = _model_metrics(y_test, predictions, class_labels)

        comparison[model_name] = {
            "accuracy": current_metrics["accuracy"],
            "precision": current_metrics["precision"],
            "recall": current_metrics["recall"],
            "f1_score": current_metrics["f1_score"],
        }

        sort_key = (current_metrics["f1_score"], current_metrics["accuracy"])
        logger.info("%s metrics: %s", model_name, comparison[model_name])

        if sort_key > best_sort_key:
            best_sort_key = sort_key
            best_name = model_name
            best_pipeline = pipeline
            best_metrics = current_metrics

    if best_pipeline is None or best_metrics is None:
        raise RuntimeError("No model could be trained.")

    metrics = {
        **best_metrics,
        "selected_model_name": best_name,
        "model_comparison": comparison,
        "class_labels": class_labels,
        "feature_columns": FEATURE_COLUMNS,
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "total_samples": int(len(df)),
    }

    bundle = {
        "pipeline": best_pipeline,
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "class_labels": class_labels,
        "feature_options": feature_options,
        "metrics": metrics,
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, model_path)
    _write_json(metrics_path, metrics)
    _write_json(Path(metrics_path).with_name("feature_info.json"), feature_options)
    if generate_plot:
        generate_visualizations(metrics["confusion_matrix"], class_labels, metrics["accuracy"])

    logger.info("Selected model: %s", best_name)
    logger.info("Saved pipeline bundle to %s", model_path)
    logger.info("Saved metrics to %s", metrics_path)
    return metrics


def load_model_bundle(model_path: Path = MODEL_PATH) -> dict[str, Any]:
    """Load the trained model bundle, training it first if necessary."""
    model_path = Path(model_path)
    if not model_path.exists():
        train_model()
    return joblib.load(model_path)


if __name__ == "__main__":
    train_model()
