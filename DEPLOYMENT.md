# Deployment Guide

## Quick Start

### Option 1: Using setup script (Recommended)

```bash
# Make the setup script executable
chmod +x setup.sh

# Run setup
sudo ./setup.sh

# Start the application
python3 app.py
```

### Option 2: Manual Installation

```bash
# Update system packages
sudo apt-get update

# Install pip if not available
sudo apt-get install python3-pip

# Install dependencies
pip3 install -r requirements.txt

# Start the application
python3 app.py
```

## Access the Application

Once started, open your browser and navigate to:
```
http://localhost:5000
```

## Initial Setup

On first run, the application will:
1. Create necessary directories (models/, data/, static/, templates/)
2. Generate a sample dataset if the Kaggle dataset is not available
3. Train the GaussianNB model
4. Generate performance metrics and visualizations

This process takes 1-2 minutes.

## Dataset Setup (Optional)

To use the actual Kaggle dataset:

1. Download from: https://www.kaggle.com/datasets/mdmahmudulhasansuzan/students-adaptability-level-in-online-education

2. Place the CSV file in the `data/` directory with the name:
   ```
   students_adaptability_level_online_education.csv
   ```

3. Restart the application or use the "Retrain Model" button

## Production Deployment

### Using Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Docker

This repo now includes a `Dockerfile` that builds the React frontend and serves it together with the Flask backend.

Build and run locally:

```bash
docker build -t student-adaptability-predictor .
docker run -p 5000:5000 student-adaptability-predictor
```

### Free live hosting options

For a live demo link, push the repository to GitHub and connect it to a free Docker-friendly host:

- Render: create a new Web Service, select Docker, and point it at this repo.
- Railway: create a new project, choose Docker, and connect the repo.

Both services will use the `Dockerfile` and expose the app on a public URL.

If the host uses a dynamic port, the app now honors the standard `PORT` environment variable.

## Environment Variables

No environment variables are required. All configuration is handled internally.

## Troubleshooting

### Port Already in Use
```bash
# Change the port in app.py or use environment variable
export PORT=8080
python3 app.py
```

### Missing Dependencies
```bash
pip3 install --upgrade -r requirements.txt
```

### Model Training Fails
```bash
# Remove old models and retrain
rm -rf models/*
python3 model_training.py
```

### Static Files Not Loading
Ensure the static/ directory exists and contains:
- styles.css
- script.js
- confusion_matrix.png (generated after training)

## Performance Optimization

- Increase Gunicorn workers: `-w 8`
- Enable caching for static files
- Use a reverse proxy (nginx) for production
- Implement Redis for session management

## Security Notes

- Change `debug=True` to `debug=False` in production
- Use HTTPS in production
- Implement rate limiting for API endpoints
- Add authentication for sensitive operations
