#!/bin/bash

echo "Installing Python dependencies..."

apt-get update -qq && apt-get install -y -qq python3-pip python3-venv

python3 -m pip install --upgrade pip

pip install flask==3.0.0
pip install flask-cors==4.0.0
pip install pandas==2.1.4
pip install numpy==1.26.2
pip install scikit-learn==1.3.2
pip install joblib==1.3.2
pip install matplotlib==3.8.2
pip install seaborn==0.13.0
pip install reportlab==4.0.7
pip install gunicorn==21.2.0

echo "Setup complete!"
echo "Run 'python3 app.py' to start the application"
