# PythonAnywhere Setup Guide

## Quick Fix for Channels Import Error

If you encounter the error:
```
ImportError: cannot import name 'DEFAULT_CHANNEL_LAYER' from 'channels'
```

Follow these steps:

### 1. Connect to PythonAnywhere Console
- Go to your PythonAnywhere dashboard
- Click on "Consoles" tab
- Start a new Bash console

### 2. Run the Setup Script
```bash
cd /home/nelsonterdoo/college_election_portal
chmod +x setup_pythonanywhere.sh
./setup_pythonanywhere.sh
```

### 3. Manual Fix (if script doesn't work)
```bash
# Navigate to project
cd /home/nelsonterdoo/college_election_portal

# Activate virtual environment
source /home/nelsonterdoo/.virtualenvs/nocen-virtualenv/bin/activate

# Remove conflicting package
pip uninstall django-channels -y

# Install correct channels version
pip install channels==4.2.2

# Install all requirements
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput
```

### 4. Reload Your Web App
- Go to "Web" tab in PythonAnywhere
- Click "Reload" button for your web app

## What Was Fixed

The issue was caused by having both:
- `channels==4.2.2` (correct, modern version)
- `django-channels==0.7.0` (old, conflicting package)

The `django-channels` package is deprecated and conflicts with the modern `channels` package.

## Verification

After setup, you should be able to:
1. Visit your app at `https://gttech.pythonanywhere.com/`
2. See the Swagger documentation at `https://gttech.pythonanywhere.com/api/docs/`
3. Access the election results endpoint at `https://gttech.pythonanywhere.com/elections/1/results/`

## Common Issues

### Issue: Still getting import errors
**Solution**: Make sure you're using the correct virtual environment:
```bash
which python
# Should show: /home/nelsonterdoo/.virtualenvs/nocen-virtualenv/bin/python
```

### Issue: WebSocket not working
**Solution**: Check if Redis is configured:
```bash
# In PythonAnywhere console
python manage.py shell
>>> from channels.layers import get_channel_layer
>>> channel_layer = get_channel_layer()
>>> print("Channels working!")
```

### Issue: Static files not loading
**Solution**: Run collectstatic again:
```bash
python manage.py collectstatic --noinput
```

## Support

If you continue to have issues:
1. Check the PythonAnywhere error logs in the "Web" tab
2. Verify your virtual environment is activated
3. Ensure all packages are installed correctly
4. Check that your WSGI file points to the correct path 