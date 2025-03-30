#!/bin/bash

# Define application directory
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

# Check if virtual environment exists, create if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
    # For Windows Git Bash compatibility
    if [ ! $? -eq 0 ]; then
        source venv/Scripts/activate
    fi
fi

# Install or update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running migrations..."
python manage.py migrate

# Start the development server
echo "Starting server..."
python manage.py runserver 0.0.0.0:8000
