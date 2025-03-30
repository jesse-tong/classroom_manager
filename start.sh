#!/bin/bash

# Define application directory
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"


# Install or update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running migrations..."
python manage.py migrate

# Start the development server
echo "Starting server..."
python manage.py runserver 0.0.0.0:8000
