# Student Adaptability ML Predictor System

A clean full-stack machine learning web application that predicts a student's adaptability level for online education. The project uses a Flask API, a scikit-learn training pipeline, and a React + Vite + TypeScript frontend.

## Project Overview

The application predicts one of three adaptivity levels:

- Low
- Moderate
- High

The prediction is based on student and learning-environment inputs such as education level, institution type, IT background, location, load-shedding, financial condition, internet type, network type, class duration, LMS access, and device.

If the original dataset is not available, the training script creates a lightweight sample dataset so the project remains runnable for demos and viva/project submission.

## Features

- Single student prediction form
- Confidence score and class probability breakdown
- Batch CSV upload with downloadable predictions
- PDF export for a single prediction report
- Model metrics dashboard
- Health check API
- Feature options served dynamically from the backend
- Proper request validation and JSON error responses
- Saved scikit-learn Pipeline with OneHotEncoder preprocessing
- Model comparison across GaussianNB, LogisticRegression, RandomForestClassifier, and GradientBoostingClassifier

## Tech Stack

Backend:

- Python
- Flask
- Flask-CORS
- pandas
- scikit-learn
- joblib
- ReportLab

Frontend:

- React
- Vite
- TypeScript
- Tailwind CSS
- lucide-react

Testing and tooling:

- Python unittest
- ESLint
- TypeScript compiler
- npm audit

## Folder Structure

```text
.
|-- app.py
|-- model_training.py
|-- requirements.txt
|-- package.json
|-- vite.config.ts
|-- tailwind.config.js
|-- index.html
|-- src/
|   |-- App.tsx
|   |-- index.css
|   |-- main.tsx
|   `-- vite-env.d.ts
|-- data/
|   `-- students_adaptability_level_online_education.csv
|-- models/
|   |-- adaptability_pipeline.joblib
|   |-- feature_info.json
|   `-- metrics.json
|-- sample_batch.csv
|-- test_api.py
|-- test_model.py
|-- generate_sample_csv.py
|-- verify_installation.py
`-- .env.example
```

## Backend Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install Python dependencies:

```bash
python -m pip install -r requirements.txt
```

Train or refresh the model:

```bash
python model_training.py
```

Run the Flask API:

```bash
python app.py
```

Default backend URL:

```text
http://localhost:5000
```

## Frontend Setup

Install Node dependencies:

```bash
npm install
```

Run the Vite development server:

```bash
npm run dev
```

Default frontend URL:

```text
http://localhost:5173
```

The Vite config proxies `/api` requests to `http://localhost:5000`, so keep the Flask server running while using the frontend in development.

After running `npm run build`, Flask can also serve the compiled frontend from `dist/` at `http://localhost:5000`.

## Environment Variables

Copy `.env.example` to `.env` if you want to customize local settings.

```text
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=true
CORS_ORIGINS=http://localhost:5173
MAX_UPLOAD_MB=2
BATCH_MAX_ROWS=1000
```

Do not commit real secrets. This project does not require secrets by default.

## Docker Deployment

This project supports Docker-based deployment, which is the best way to publish both the Flask API and built React frontend together.

Build and run locally:

```bash
docker build -t student-adaptability-predictor .
docker run -p 5000:5000 student-adaptability-predictor
```

Then open:

```text
http://localhost:5000
```

For a free live demo, push this repository to GitHub and connect it to a free Docker-capable host like Render or Railway. The repo already includes a `Dockerfile` and `Procfile`.

## API Endpoints

### GET `/api/health`

Returns API status and whether model/metrics files are available.

### GET `/api/feature-info`

Returns feature names, valid options, feature order, and target labels.

### POST `/api/predict`

Predicts a single student adaptivity level.

Example body:

```json
{
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
  "Device": "Computer"
}
```

### POST `/api/predict-batch`

Accepts a CSV file in multipart form data under the `file` field. The CSV must contain all feature columns shown in `sample_batch.csv`.

### POST `/api/export-pdf`

Creates a PDF report from `student_data` and `prediction_result` objects.

### GET `/api/metrics`

Returns model accuracy, precision, recall, F1-score, confusion matrix, classification report, train/test counts, selected model name, and model comparison results.

### POST `/api/retrain`

Retrains the model and reloads the saved pipeline for the current Flask process.

## Testing and Quality Checks

Run Python tests:

```bash
python -m unittest test_model.py test_api.py
```

Run frontend type checks:

```bash
npm run typecheck
```

Run frontend linting:

```bash
npm run lint
```

Build frontend assets:

```bash
npm run build
```

Check dependency audit:

```bash
npm audit
```

## Screenshots

Add screenshots here before submitting on GitHub:

- Dashboard view
- Single prediction form and result
- Batch CSV upload
- Model metrics section

## Current Model Output

The included generated sample dataset selects `LogisticRegression` as the best model:

- Accuracy: 77.59%
- Precision: 77.77%
- Recall: 77.59%
- F1-score: 77.67%
- Train samples: 964
- Test samples: 241

Metrics are saved in `models/metrics.json`.

## Future Improvements

- Replace the generated sample dataset with the original Kaggle dataset.
- Add cross-validation for more reliable model selection.
- Add downloadable CSV templates from the frontend.
- Add charts for class probabilities and model comparison.
- Add a short project report notebook for academic submission.

## License

This project is intended for educational and portfolio use.
