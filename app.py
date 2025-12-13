"""
Flask Application for Student Adaptability Level Prediction
Provides REST API endpoints for ML predictions and model management
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import pandas as pd
import joblib
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import model_training

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

MODEL_PATH = 'models/adaptability_model.pkl'
ENCODER_PATH = 'models/label_encoders.pkl'
METRICS_PATH = 'models/metrics.json'

def load_model_and_encoders():
    """Load the trained model and label encoders"""
    try:
        if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODER_PATH):
            logger.warning("Model not found. Training new model...")
            model_training.train_model()

        model = joblib.load(MODEL_PATH)
        encoders = joblib.load(ENCODER_PATH)

        with open(METRICS_PATH, 'r') as f:
            metrics = json.load(f)

        return model, encoders, metrics
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise

model, encoders, metrics = load_model_and_encoders()

FEATURE_ORDER = [
    'Gender', 'Age', 'Education Level', 'Institution Type', 'IT Student',
    'Location', 'Load-shedding', 'Financial Condition', 'Internet Type',
    'Network Type', 'Class Duration', 'Self Lms', 'Device'
]

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Predict adaptability level for a single student
    Expected JSON format: {feature_name: feature_value, ...}
    Returns: {prediction: str, confidence: float, probabilities: dict}
    """
    try:
        data = request.json
        logger.info(f"Received prediction request: {data}")

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        features = []
        for feature in FEATURE_ORDER:
            if feature not in data:
                return jsonify({'error': f'Missing feature: {feature}'}), 400

            value = data[feature]
            if feature in encoders:
                if value not in encoders[feature].classes_:
                    return jsonify({'error': f'Invalid value for {feature}: {value}'}), 400
                encoded_value = encoders[feature].transform([value])[0]
            else:
                encoded_value = value

            features.append(encoded_value)

        features_array = pd.DataFrame([features], columns=FEATURE_ORDER)

        prediction = model.predict(features_array)[0]
        probabilities = model.predict_proba(features_array)[0]

        predicted_label = encoders['Adaptivity Level'].inverse_transform([prediction])[0]

        class_labels = encoders['Adaptivity Level'].classes_
        prob_dict = {label: float(prob) for label, prob in zip(class_labels, probabilities)}

        confidence = float(max(probabilities) * 100)

        result = {
            'prediction': predicted_label,
            'confidence': round(confidence, 2),
            'probabilities': {k: round(v * 100, 2) for k, v in prob_dict.items()},
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"Prediction result: {result}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-batch', methods=['POST'])
def predict_batch():
    """
    Predict adaptability levels for multiple students from CSV file
    Expected: multipart/form-data with 'file' field containing CSV
    Returns: CSV file with predictions
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400

        df = pd.read_csv(file)
        logger.info(f"Batch prediction for {len(df)} records")

        for feature in FEATURE_ORDER:
            if feature not in df.columns:
                return jsonify({'error': f'Missing column: {feature}'}), 400

        encoded_df = df.copy()
        for feature in FEATURE_ORDER:
            if feature in encoders:
                try:
                    encoded_df[feature] = encoders[feature].transform(df[feature])
                except ValueError as e:
                    return jsonify({'error': f'Invalid values in column {feature}'}), 400

        X = encoded_df[FEATURE_ORDER]
        predictions = model.predict(X)
        probabilities = model.predict_proba(X)

        predicted_labels = encoders['Adaptivity Level'].inverse_transform(predictions)

        df['Predicted_Adaptivity'] = predicted_labels
        df['Confidence'] = [round(max(prob) * 100, 2) for prob in probabilities]

        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'predictions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-pdf', methods=['POST'])
def export_pdf():
    """
    Export prediction results to PDF
    Expected JSON: {student_data: {...}, prediction_result: {...}}
    Returns: PDF file
    """
    try:
        data = request.json

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        title = Paragraph("Student Adaptability Prediction Report", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 20))

        timestamp = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
        elements.append(timestamp)
        elements.append(Spacer(1, 20))

        if 'student_data' in data:
            student_data = [[k, str(v)] for k, v in data['student_data'].items()]
            student_table = Table([['Feature', 'Value']] + student_data)
            student_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(student_table)
            elements.append(Spacer(1, 20))

        if 'prediction_result' in data:
            result = data['prediction_result']
            prediction_text = Paragraph(f"<b>Predicted Adaptivity Level:</b> {result.get('prediction', 'N/A')}", styles['Heading2'])
            elements.append(prediction_text)
            elements.append(Spacer(1, 10))

            confidence_text = Paragraph(f"<b>Confidence:</b> {result.get('confidence', 0)}%", styles['Normal'])
            elements.append(confidence_text)
            elements.append(Spacer(1, 10))

            if 'probabilities' in result:
                prob_data = [['Level', 'Probability']]
                for level, prob in result['probabilities'].items():
                    prob_data.append([level, f"{prob}%"])

                prob_table = Table(prob_data)
                prob_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(prob_table)

        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'prediction_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )

    except Exception as e:
        logger.error(f"PDF export error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get model performance metrics"""
    try:
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error retrieving metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/retrain', methods=['POST'])
def retrain_model():
    """Retrain the model with current data"""
    try:
        logger.info("Starting model retraining...")

        result = model_training.train_model()

        global model, encoders, metrics
        model, encoders, metrics = load_model_and_encoders()

        return jsonify({
            'status': 'success',
            'message': 'Model retrained successfully',
            'metrics': metrics
        })

    except Exception as e:
        logger.error(f"Retraining error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/feature-info', methods=['GET'])
def get_feature_info():
    """Get information about available features and their possible values"""
    try:
        feature_info = {}
        for feature in FEATURE_ORDER:
            if feature in encoders:
                feature_info[feature] = encoders[feature].classes_.tolist()
            else:
                feature_info[feature] = "numeric"

        return jsonify(feature_info)

    except Exception as e:
        logger.error(f"Error retrieving feature info: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('models', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)

    app.run(debug=True, host='0.0.0.0', port=5000)
