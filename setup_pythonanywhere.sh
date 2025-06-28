#!/bin/bash

# Setup script for College Election Portal on PythonAnywhere
echo "Setting up College Election Portal on PythonAnywhere..."

# Navigate to project directory
cd /home/nelsonterdoo/college_election_portal

# Activate virtual environment
source /home/nelsonterdoo/.virtualenvs/nocen-virtualenv/bin/activate

# Remove conflicting packages
echo "Removing conflicting packages..."
pip uninstall django-channels -y

# Install/upgrade channels to compatible version
echo "Installing compatible channels version..."
pip install channels==4.2.2

# Install other requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Setup complete! You can now reload your web app on PythonAnywhere." 