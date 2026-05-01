# Quick Start Guide

## Installation & Setup

### Prerequisites
- Python 3.13+ installed
- pip package manager

### Step 1: Install Dependencies

**Option A - Using setup script (Recommended):**
```bash
chmod +x setup.sh
sudo ./setup.sh
```

**Option B - Manual installation:**
```bash
# Install pip if needed
sudo apt-get update
sudo apt-get install python3-pip

# Install Python packages
pip3 install flask flask-cors pandas numpy scikit-learn joblib matplotlib seaborn reportlab
```

### Step 2: Start the Application

```bash
python3 app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
```

### Step 3: Open in Browser

Navigate to: **http://localhost:5000**

## First Time Setup

When you start the application for the first time:

1. The app will create necessary directories
2. Generate a sample dataset (1,205 records)
3. Train the GaussianNB model
4. Generate performance metrics

**This takes about 1-2 minutes.**

## Using the Application

### Single Prediction

1. Click **"Single Prediction"** tab
2. Fill in all 13 student features:
   - Demographics (Gender, Age)
   - Education (Level, Institution Type)
   - Technical (IT Student, Device, Internet)
   - Environment (Location, Load-shedding, Financial Condition)
   - Learning (Class Duration, Self LMS)
3. Click **"Predict Adaptability"**
4. View results with confidence scores
5. Export as PDF if needed

### Batch Prediction

1. Click **"Batch Upload"** tab
2. Generate sample CSV:
   ```bash
   python3 generate_sample_csv.py
   ```
3. Upload the generated `sample_batch.csv`
4. Download results with predictions

### View Model Metrics

1. Click **"Model Metrics"** tab
2. View:
   - Accuracy, Precision, Recall, F1-Score
   - Confusion Matrix
   - Classification Report
3. Click **"Retrain Model"** to update the model

## Testing

### Test Model Training
```bash
python3 test_model.py
```

### Test API Endpoints
```bash
# Start the application first
python3 app.py

# In another terminal
python3 test_api.py
```

### Generate Sample Data
```bash
python3 generate_sample_csv.py
```

## Expected Results

- **Model Accuracy**: ~67%
- **Classes**: Low, Moderate, High
- **Train/Test Split**: 80/20 (964/241 samples)

## Troubleshooting

### Port 5000 Already in Use
```bash
# Edit app.py, change the port at the bottom:
app.run(debug=True, host='0.0.0.0', port=8080)
```

### Module Not Found
```bash
pip3 install --upgrade -r requirements.txt
```

### Permission Denied
```bash
sudo python3 app.py
# or
chmod +x setup.sh
```

### Static Files Not Loading
Check that these directories exist:
- `static/` (with styles.css, script.js)
- `templates/` (with index.html)
- `models/` (will be created automatically)
- `data/` (will be created automatically)

## File Structure

```
project/
├── app.py                      # Main Flask application
├── model_training.py           # ML model training
├── requirements.txt            # Python dependencies
├── README.md                   # Full documentation
├── QUICKSTART.md              # This file
├── DEPLOYMENT.md              # Deployment guide
├── setup.sh                   # Setup script
├── test_model.py              # Model testing
├── test_api.py                # API testing
├── generate_sample_csv.py     # Sample data generator
├── data/                      # Dataset storage
├── models/                    # Trained models
├── static/                    # CSS, JS, images
│   ├── styles.css
│   ├── script.js
│   └── confusion_matrix.png
└── templates/                 # HTML templates
    └── index.html
```

## Next Steps

1. ✅ Start the application: `python3 app.py`
2. ✅ Open http://localhost:5000
3. ✅ Make your first prediction
4. ✅ Upload a batch CSV file
5. ✅ View model metrics
6. ✅ Export results as PDF

## Support

For issues or questions:
- Check DEPLOYMENT.md for detailed deployment instructions
- Review README.md for comprehensive documentation
- Run test scripts to verify functionality

## Features

✓ Single student prediction with confidence scores
✓ Batch CSV upload for multiple predictions
✓ PDF export for prediction reports
✓ Real-time model metrics and visualizations
✓ Confusion matrix display
✓ Model retraining capability
✓ Responsive, modern UI
✓ Error handling and validation
✓ Comprehensive API endpoints

Happy predicting! 🎓
