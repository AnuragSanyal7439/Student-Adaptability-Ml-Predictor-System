"""
Quick local verification for the Student Adaptability ML Predictor project.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def check_file(path: str, description: str) -> bool:
    exists = (ROOT / path).is_file()
    status = "OK" if exists else "MISSING"
    print(f"{status:8} {description}: {path}")
    return exists


def check_package(package_name: str) -> bool:
    exists = importlib.util.find_spec(package_name) is not None
    status = "OK" if exists else "MISSING"
    print(f"{status:8} Python package: {package_name}")
    return exists


def main() -> int:
    print("Student Adaptability ML Predictor - Installation Check")
    print("=" * 60)

    files = [
        ("app.py", "Flask API"),
        ("model_training.py", "ML training pipeline"),
        ("requirements.txt", "Python dependencies"),
        ("package.json", "Frontend package config"),
        ("vite.config.ts", "Vite config"),
        ("tailwind.config.js", "Tailwind config"),
        ("src/main.tsx", "React entry point"),
        ("src/App.tsx", "React app"),
        ("src/index.css", "Tailwind stylesheet"),
        ("test_api.py", "API tests"),
        ("test_model.py", "Model tests"),
        ("sample_batch.csv", "Batch CSV sample"),
        (".env.example", "Environment example"),
        ("README.md", "Project documentation"),
    ]

    file_results = [check_file(path, description) for path, description in files]

    print("\nPython packages")
    print("-" * 60)
    package_results = [
        check_package(name)
        for name in [
            "flask",
            "flask_cors",
            "pandas",
            "numpy",
            "sklearn",
            "joblib",
            "reportlab",
        ]
    ]

    all_ok = all(file_results) and all(package_results)
    print("\nSummary")
    print("-" * 60)
    print("Ready" if all_ok else "Setup incomplete")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
