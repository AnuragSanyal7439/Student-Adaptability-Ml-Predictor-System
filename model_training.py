"""
Machine Learning Model Training Script
Preprocesses data, trains GaussianNB classifier, and generates performance metrics
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    precision_recall_fscore_support
)
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATASET_PATH = 'data/students_adaptability_level_online_education.csv'
MODEL_PATH = 'models/adaptability_model.pkl'
ENCODER_PATH = 'models/label_encoders.pkl'
METRICS_PATH = 'models/metrics.json'
CONFUSION_MATRIX_PATH = 'static/confusion_matrix.png'

FEATURE_COLUMNS = [
    'Gender', 'Age', 'Education Level', 'Institution Type', 'IT Student',
    'Location', 'Load-shedding', 'Financial Condition', 'Internet Type',
    'Network Type', 'Class Duration', 'Self Lms', 'Device'
]

TARGET_COLUMN = 'Adaptivity Level'

def create_sample_dataset():
    """
    Create a sample dataset if the actual dataset is not available
    This allows the application to run without the Kaggle dataset
    """
    logger.info("Creating sample dataset...")

    np.random.seed(42)
    n_samples = 1205

    data = {
        'Gender': np.random.choice(['Boy', 'Girl'], n_samples),
        'Age': np.random.choice(['1-5', '6-10', '11-15', '16-20', '21-25', '26-30'], n_samples),
        'Education Level': np.random.choice(['School', 'College', 'University'], n_samples),
        'Institution Type': np.random.choice(['Government', 'Non Government'], n_samples),
        'IT Student': np.random.choice(['Yes', 'No'], n_samples),
        'Location': np.random.choice(['Yes', 'No'], n_samples),
        'Load-shedding': np.random.choice(['Low', 'High'], n_samples),
        'Financial Condition': np.random.choice(['Poor', 'Mid', 'Rich'], n_samples),
        'Internet Type': np.random.choice(['Mobile Data', 'Wifi', '2G', '3G', '4G'], n_samples),
        'Network Type': np.random.choice(['2G', '3G', '4G'], n_samples),
        'Class Duration': np.random.choice(['0', '1-3', '3-6'], n_samples),
        'Self Lms': np.random.choice(['Yes', 'No'], n_samples),
        'Device': np.random.choice(['Mobile', 'Tab', 'Computer'], n_samples),
    }

    weights_low = (
        (data['Financial Condition'] == 'Poor').astype(int) * 0.3 +
        (data['Internet Type'] == '2G').astype(int) * 0.2 +
        (data['Load-shedding'] == 'High').astype(int) * 0.2 +
        (data['Device'] == 'Mobile').astype(int) * 0.15 +
        (data['Self Lms'] == 'No').astype(int) * 0.15
    )

    weights_high = (
        (data['Financial Condition'] == 'Rich').astype(int) * 0.3 +
        (data['Internet Type'] == 'Wifi').astype(int) * 0.2 +
        (data['Network Type'] == '4G').astype(int) * 0.2 +
        (data['Device'] == 'Computer').astype(int) * 0.15 +
        (data['Self Lms'] == 'Yes').astype(int) * 0.15
    )

    adaptivity = []
    for low, high in zip(weights_low, weights_high):
        rand = np.random.random()
        if high > 0.6 and rand > 0.3:
            adaptivity.append('High')
        elif low > 0.6 and rand > 0.3:
            adaptivity.append('Low')
        else:
            adaptivity.append('Moderate')

    data[TARGET_COLUMN] = adaptivity

    df = pd.DataFrame(data)

    os.makedirs('data', exist_ok=True)
    df.to_csv(DATASET_PATH, index=False)
    logger.info(f"Sample dataset created with {len(df)} records")

    return df

def load_and_preprocess_data():
    """
    Load dataset and handle missing values
    Returns: DataFrame with cleaned data
    """
    logger.info("Loading dataset...")

    if not os.path.exists(DATASET_PATH):
        logger.warning(f"Dataset not found at {DATASET_PATH}. Creating sample dataset...")
        df = create_sample_dataset()
    else:
        df = pd.read_csv(DATASET_PATH)

    logger.info(f"Dataset loaded: {df.shape}")
    logger.info(f"Columns: {df.columns.tolist()}")

    initial_rows = len(df)
    df = df.dropna()
    logger.info(f"Dropped {initial_rows - len(df)} rows with missing values")

    logger.info(f"Target distribution:\n{df[TARGET_COLUMN].value_counts()}")

    return df

def encode_features(df):
    """
    Encode categorical features using LabelEncoder
    Returns: encoded DataFrame, dictionary of encoders
    """
    logger.info("Encoding categorical features...")

    encoders = {}
    df_encoded = df.copy()

    columns_to_encode = FEATURE_COLUMNS + [TARGET_COLUMN]

    for column in columns_to_encode:
        if column in df.columns:
            le = LabelEncoder()
            df_encoded[column] = le.fit_transform(df[column].astype(str))
            encoders[column] = le
            logger.info(f"Encoded {column}: {len(le.classes_)} unique values")

    return df_encoded, encoders

def train_model():
    """
    Main training function:
    - Load and preprocess data
    - Encode features
    - Split train/test (80/20)
    - Train GaussianNB
    - Generate metrics and visualizations
    """
    logger.info("Starting model training pipeline...")

    df = load_and_preprocess_data()

    df_encoded, encoders = encode_features(df)

    X = df_encoded[FEATURE_COLUMNS]
    y = df_encoded[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    logger.info(f"Training set: {X_train.shape}, Test set: {X_test.shape}")

    model = GaussianNB()
    model.fit(X_train, y_train)
    logger.info("Model training completed")

    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    logger.info(f"Model Accuracy: {accuracy:.4f}")

    cm = confusion_matrix(y_test, y_pred)
    logger.info(f"Confusion Matrix:\n{cm}")

    target_names = encoders[TARGET_COLUMN].classes_
    report = classification_report(y_test, y_pred, target_names=target_names, output_dict=True)

    precision, recall, f1, support = precision_recall_fscore_support(
        y_test, y_pred, average='weighted'
    )

    metrics = {
        'accuracy': round(accuracy * 100, 2),
        'precision': round(precision * 100, 2),
        'recall': round(recall * 100, 2),
        'f1_score': round(f1 * 100, 2),
        'confusion_matrix': cm.tolist(),
        'class_labels': target_names.tolist(),
        'classification_report': report,
        'train_samples': int(len(X_train)),
        'test_samples': int(len(X_test))
    }

    os.makedirs('models', exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(encoders, ENCODER_PATH)

    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Model saved to {MODEL_PATH}")
    logger.info(f"Encoders saved to {ENCODER_PATH}")
    logger.info(f"Metrics saved to {METRICS_PATH}")

    generate_visualizations(cm, target_names, accuracy)

    return metrics

def generate_visualizations(cm, class_labels, accuracy):
    """
    Generate confusion matrix visualization
    """
    logger.info("Generating visualizations...")

    os.makedirs('static', exist_ok=True)

    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm,
        annot=True,
        fmt='d',
        cmap='Blues',
        xticklabels=class_labels,
        yticklabels=class_labels,
        cbar_kws={'label': 'Count'}
    )
    plt.title(f'Confusion Matrix\nAccuracy: {accuracy:.2%}', fontsize=16, fontweight='bold')
    plt.ylabel('True Label', fontsize=12)
    plt.xlabel('Predicted Label', fontsize=12)
    plt.tight_layout()
    plt.savefig(CONFUSION_MATRIX_PATH, dpi=100, bbox_inches='tight')
    plt.close()

    logger.info(f"Confusion matrix saved to {CONFUSION_MATRIX_PATH}")

if __name__ == '__main__':
    train_model()
