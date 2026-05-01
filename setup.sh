#!/bin/bash

set -e

echo "Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

if command -v npm >/dev/null 2>&1; then
  echo "Installing frontend dependencies..."
  npm install
else
  echo "npm was not found. Install Node.js before running the React frontend."
fi

echo "Training model artifact..."
python3 model_training.py

echo "Setup complete."
echo "Backend:  python3 app.py"
echo "Frontend: npm run dev"
