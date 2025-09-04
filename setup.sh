#!/bin/bash

# Sustainable Travel Planner Setup Script
# This script sets up a Python virtual environment, installs dependencies, and downloads the required spaCy model.

set -e

# Function to print error messages
function error_exit {
  echo "[ERROR] $1" 1>&2
  exit 1
}

# Create virtual environment
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv || error_exit "Failed to create virtual environment. Ensure Python 3 is installed."
else
  echo "Virtual environment already exists."
fi

# Activate virtual environment
source venv/bin/activate || error_exit "Failed to activate virtual environment."

# Upgrade pip
pip install --upgrade pip || error_exit "Failed to upgrade pip."

# Install dependencies
if [ -f "requirements.txt" ]; then
  echo "Installing dependencies from requirements.txt..."
  pip install -r requirements.txt || error_exit "Failed to install dependencies."
else
  error_exit "requirements.txt not found."
fi

# Download spaCy English model
python -m spacy download en_core_web_sm || error_exit "Failed to download spaCy model."

echo "Setup complete! Activate your environment with: source venv/bin/activate"
