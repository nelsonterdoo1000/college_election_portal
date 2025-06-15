# College Election Portal API Documentation

## Table of Contents
1. [Authentication](#authentication)
2. [Elections](#elections)
3. [Positions](#positions)
4. [Candidates](#candidates)
5. [Voting](#voting)
6. [Real-time Updates](#real-time-updates)
7. [Error Handling](#error-handling)

## Authentication

### Login
```http
POST /api/auth/login/
```
Request body:
```json
{
    "username": "string",
    "password": "string"
}
```
Response (200 OK):
```json
{
    "refresh": "string",
    "access": "string",
    "user": {
        "id": "integer",
        "username": "string",
        "email": "string",
        "role": "string",
        "first_name": "string",
        "last_name": "string"
    }
}
```

### Logout
```http
POST /api/auth/logout/
```
Request body:
```json
{
    "refresh": "string"
}
```
Response (205 Reset Content)

### Refresh Token
```http
POST /api/auth/token/refresh/
```
Request body:
```json
{
    "refresh": "string"
}
```
Response (200 OK):
```json
{
    "access": "string"
}
```

## Elections

### List Elections
```http
GET /api/elections/
```
Headers:
```
Authorization: Bearer <access_token>
```
Response (200 OK):
```json
[
    {
        "id": "integer",
        "title": "string",
        "description": "string",
        "start_datetime": "datetime",
        "end_datetime": "datetime",
        "status": "string",
        "created_by": {
            "id": "integer",
            "username": "string"
        },
        "positions": [
            {
                "id": "integer",
                "title": "string",
                "description": "string",
                "candidates": [
                    {
                        "id": "integer",
                        "name": "string",
                        "bio": "string",
                        "photo": "string"
                    }
                ]
            }
        ]
    }
]
```

### Get Election Details
```http
GET /api/elections/{id}/
```
Response (200 OK):
```json
{
    "id": "integer",
    "title": "string",
    "description": "string",
    "start_datetime": "datetime",
    "end_datetime": "datetime",
    "status": "string",
    "created_by": {
        "id": "integer",
        "username": "string"
    },
    "positions": [...]
}
```

### Create Election
```http
POST /api/elections/
```
Request body:
```json
{
    "title": "string",
    "description": "string",
    "start_datetime": "datetime",
    "end_datetime": "datetime"
}
```
Response (201 Created):
```json
{
    "id": "integer",
    "title": "string",
    ...
}
```

### Start Election
```http
POST /api/elections/{id}/start/
```
Response (200 OK):
```json
{
    "status": "election started"
}
```

### End Election
```http
POST /api/elections/{id}/end/
```
Response (200 OK):
```json
{
    "status": "election ended"
}
```

### Get Election Results
```http
GET /api/elections/{id}/results/
```
Response (200 OK):
```json
{
    "id": "integer",
    "title": "string",
    "positions": [
        {
            "position_id": "integer",
            "position_title": "string",
            "candidates": [
                {
                    "candidate_id": "integer",
                    "candidate_name": "string",
                    "vote_count": "integer"
                }
            ]
        }
    ]
}
```

## Positions

### List Positions
```http
GET /api/elections/{election_id}/positions/
```
Response (200 OK):
```json
[
    {
        "id": "integer",
        "title": "string",
        "description": "string",
        "election": "integer",
        "candidates": [...]
    }
]
```

### Create Position
```http
POST /api/elections/{election_id}/positions/
```
Request body:
```json
{
    "title": "string",
    "description": "string"
}
```
Response (201 Created):
```json
{
    "id": "integer",
    "title": "string",
    ...
}
```

## Candidates

### List Candidates
```http
GET /api/elections/{election_id}/positions/{position_id}/candidates/
```
Response (200 OK):
```json
[
    {
        "id": "integer",
        "name": "string",
        "bio": "string",
        "photo": "string",
        "position": "integer"
    }
]
```

### Create Candidate
```http
POST /api/elections/{election_id}/positions/{position_id}/candidates/
```
Request body:
```json
{
    "name": "string",
    "bio": "string",
    "photo": "file"
}
```
Response (201 Created):
```json
{
    "id": "integer",
    "name": "string",
    ...
}
```

## Voting

### Cast Vote
```http
POST /api/votes/
```
Request body:
```json
{
    "election": "integer",
    "position": "integer",
    "candidate": "integer"
}
```
Response (201 Created):
```json
{
    "id": "integer",
    "election": "integer",
    "position": "integer",
    "candidate": "integer",
    "student": "integer",
    "timestamp": "datetime"
}
```

### List User's Votes
```http
GET /api/votes/
```
Response (200 OK):
```json
[
    {
        "id": "integer",
        "election": "integer",
        "position": "integer",
        "candidate": "integer",
        "timestamp": "datetime"
    }
]
```

## Real-time Updates

### WebSocket Connection
```javascript
const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
const ws_path = `${ws_scheme}://${window.location.host}/ws/public/elections/${election_id}/live-results/`;
const socket = new WebSocket(ws_path);
```

Message format:
```json
{
    "type": "election_results_update",
    "results": {
        "id": "integer",
        "title": "string",
        "positions": [
            {
                "position_id": "integer",
                "position_title": "string",
                "candidates": [
                    {
                        "candidate_id": "integer",
                        "candidate_name": "string",
                        "vote_count": "integer"
                    }
                ]
            }
        ]
    }
}
```

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
    "error": "string"
}
```

#### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

#### 403 Forbidden
```json
{
    "detail": "You do not have permission to perform this action."
}
```

#### 404 Not Found
```json
{
    "detail": "Not found."
}
```

### Common Error Messages
- "Invalid credentials"
- "Can only vote in active elections"
- "Results are only available for active or completed elections"
- "Only pending elections can be started"
- "Only active elections can be ended"
- "Invalid election, position, or candidate"

## Authentication Flow

1. User logs in with username and password
2. Server returns access token and refresh token
3. Client includes access token in Authorization header for all requests
4. When access token expires, client uses refresh token to get new access token
5. For logout, client sends refresh token to be blacklisted

## Best Practices

1. Always include the Authorization header:
```
Authorization: Bearer <access_token>
```

2. Handle token expiration:
   - Store refresh token securely
   - Implement automatic token refresh
   - Handle 401 responses appropriately

3. WebSocket connection:
   - Implement reconnection logic
   - Handle connection errors
   - Validate incoming messages

4. Error handling:
   - Check response status codes
   - Parse error messages
   - Implement appropriate user feedback 