# Student Adaptability ML Predictor

AI-powered prediction system for assessing student adaptability levels in online education environments using Machine Learning.

## Features

- **Single Prediction**: Input individual student data for instant adaptability predictions
- **Batch Processing**: Upload CSV files for bulk predictions
- **PDF Export**: Generate detailed prediction reports
- **Model Metrics**: View comprehensive performance metrics and confusion matrix
- **Model Retraining**: Retrain the model with updated data
- **Responsive Design**: Modern, mobile-friendly interface

## Technology Stack

- **Backend**: Flask (Python)
- **ML Algorithm**: Gaussian Naive Bayes (scikit-learn)
- **Frontend**: HTML, CSS, JavaScript
- **Visualization**: Matplotlib, Seaborn
- **PDF Generation**: ReportLab

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open browser and navigate to:
```
http://localhost:5000
```

## Dataset

The application uses the "Students Adaptability Level in Online Education" dataset from Kaggle with 1,205 records and 14 features:

- Gender
- Age
- Education Level
- Institution Type
- IT Student
- Location
- Load-shedding
- Financial Condition
- Internet Type
- Network Type
- Class Duration
- Self LMS
- Device

**Target Variable**: Adaptivity Level (Low, Moderate, High)

## Model Performance

- **Algorithm**: Gaussian Naive Bayes
- **Train/Test Split**: 80/20
- **Expected Accuracy**: ~67%

## API Endpoints

### POST /api/predict
Single student prediction
```json
{
  "Gender": "Boy",
  "Age": "21-25",
  "Education Level": "University",
  ...
}
```

### POST /api/predict-batch
Batch CSV upload for multiple predictions

### POST /api/export-pdf
Export prediction results to PDF

### GET /api/metrics
Get model performance metrics

### POST /api/retrain
Retrain the machine learning model

### GET /api/feature-info
Get available feature values for form population

## Project Structure

```
project/
├── app.py                  # Flask application
├── model_training.py       # ML model training script
├── requirements.txt        # Python dependencies
├── README.md              # Documentation
├── data/                  # Dataset storage
├── models/                # Trained models and encoders
├── static/                # CSS, JS, images
│   ├── styles.css
│   ├── script.js
│   └── confusion_matrix.png
└── templates/             # HTML templates
    └── index.html
```

## Usage

### Single Prediction

1. Navigate to "Single Prediction" tab
2. Fill in all student information fields
3. Click "Predict Adaptability"
4. View results with confidence scores
5. Export results as PDF if needed

### Batch Prediction

1. Navigate to "Batch Upload" tab
2. Upload a CSV file with student data
3. Download the results CSV with predictions

### View Metrics

1. Navigate to "Model Metrics" tab
2. View accuracy, precision, recall, F1-score
3. Analyze confusion matrix
4. Review classification report
5. Retrain model if needed

## CSV Format for Batch Upload

Your CSV must include these columns:
- Gender
- Age
- Education Level
- Institution Type
- IT Student
- Location
- Load-shedding
- Financial Condition
- Internet Type
- Network Type
- Class Duration
- Self Lms
- Device

## Notes

- If the Kaggle dataset is not available, the application automatically generates a sample dataset
- The model is trained on first run and saved for subsequent predictions
- All categorical features are automatically encoded
- Missing values are handled during preprocessing

## License

Educational use only.
