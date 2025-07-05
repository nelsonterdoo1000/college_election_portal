# JWT Authentication Troubleshooting Guide

## Overview
This guide helps you troubleshoot JWT authentication and refresh token issues in the College Election Portal.

## Common Issues and Solutions

### 1. Refresh Token Not Working

**Symptoms:**
- Getting 401 errors when trying to refresh tokens
- "Token is invalid or expired" errors
- Blacklist functionality not working

**Root Cause:**
The JWT blacklist app was not properly configured in the Django settings.

**Solution:**
1. Ensure `rest_framework_simplejwt.token_blacklist` is in `INSTALLED_APPS`
2. Run migrations for the blacklist app
3. Restart the Django server

```bash
# Run the setup script
python setup_jwt_blacklist.py

# Or manually run migrations
python manage.py makemigrations rest_framework_simplejwt
python manage.py migrate rest_framework_simplejwt
python manage.py migrate
```

### 2. Token Expiration Issues

**Symptoms:**
- Access tokens expiring too quickly
- Refresh tokens not being accepted

**Solution:**
Check the JWT settings in `settings.py`:

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # 1 hour
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),     # 1 day
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

### 3. Authentication Flow

**Proper Authentication Flow:**

1. **Login:**
```bash
POST /api/auth/login/
{
    "username": "your_username",
    "password": "your_password"
}
```

2. **Use Access Token:**
```bash
GET /api/elections/
Authorization: Bearer <access_token>
```

3. **Refresh Token (when access token expires):**
```bash
POST /api/auth/token/refresh/
{
    "refresh": "your_refresh_token"
}
```

4. **Logout:**
```bash
POST /api/auth/logout/
{
    "refresh": "your_refresh_token"
}
```

### 4. Testing JWT Functionality

**Test Script:**
```python
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_jwt_flow():
    # 1. Login
    login_data = {
        "username": "admin",
        "password": "your_password"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens['access']
        refresh_token = tokens['refresh']
        print("Login successful")
        print(f"Access token: {access_token[:50]}...")
        print(f"Refresh token: {refresh_token[:50]}...")
        
        # 2. Use access token
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/elections/", headers=headers)
        print(f"API call status: {response.status_code}")
        
        # 3. Refresh token
        refresh_data = {"refresh": refresh_token}
        response = requests.post(f"{BASE_URL}/auth/token/refresh/", json=refresh_data)
        if response.status_code == 200:
            new_access_token = response.json()['access']
            print("Token refresh successful")
            print(f"New access token: {new_access_token[:50]}...")
        
        # 4. Logout
        logout_data = {"refresh": refresh_token}
        response = requests.post(f"{BASE_URL}/auth/logout/", json=logout_data)
        print(f"Logout status: {response.status_code}")
        
    else:
        print(f"Login failed: {response.status_code}")

if __name__ == "__main__":
    test_jwt_flow()
```

### 5. Database Issues

**Check if blacklist tables exist:**
```sql
-- PostgreSQL
\dt *blacklist*

-- Should show tables like:
-- rest_framework_simplejwt_token_blacklist_blacklistedtoken
-- rest_framework_simplejwt_token_blacklist_outstandingtoken
```

**If tables don't exist:**
```bash
python manage.py migrate rest_framework_simplejwt
```

### 6. Environment Variables

**Ensure these are set:**
```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost:5432/election_portal
```

### 7. Debugging Tips

**Enable Debug Logging:**
Add to `settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'rest_framework_simplejwt': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

**Check Token Validity:**
```python
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

try:
    token = RefreshToken(refresh_token)
    print("Token is valid")
except TokenError as e:
    print(f"Token error: {e}")
```

### 8. Common Error Messages

- **"Token is invalid or expired"**: Refresh token has expired or is invalid
- **"Token is blacklisted"**: Token was used for logout and is now blacklisted
- **"Authentication credentials were not provided"**: Missing Authorization header
- **"Invalid token header"**: Incorrect Authorization header format

### 9. Production Considerations

1. **Use HTTPS** in production
2. **Set appropriate token lifetimes**
3. **Monitor blacklist table size**
4. **Implement token cleanup** for expired tokens
5. **Use secure secret keys**

### 10. Getting Help

If you're still experiencing issues:

1. Check the Django logs for detailed error messages
2. Verify all migrations have been applied
3. Test with a fresh database
4. Ensure Redis is running (for blacklist functionality)
5. Check if the JWT library version is compatible

**Useful Commands:**
```bash
# Check Django version
python -c "import django; print(django.get_version())"

# Check JWT library version
python -c "import rest_framework_simplejwt; print(rest_framework_simplejwt.__version__)"

# Check installed apps
python manage.py shell -c "from django.conf import settings; print(settings.INSTALLED_APPS)"
``` 