# College Election Portal

A secure and transparent web-based platform for conducting college elections with real-time results display.

## Features

- Secure user authentication and role-based access control
- Election management (create, configure, monitor)
- Real-time vote counting and results display
- Anonymous voting system
- Comprehensive audit logging
- RESTful API
- WebSocket support for real-time updates

## Technology Stack

- Backend: Python 3.x, Django, Django REST Framework
- Real-time: Django Channels, WebSockets
- Database: PostgreSQL
- Caching/Message Broker: Redis
- Frontend: (To be implemented - React/Vue.js)

## Prerequisites

- Python 3.x
- PostgreSQL
- Redis
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd college_election_portal
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following variables:
```
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/election_portal
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

5. Set up the database:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

## Running the Development Server

1. Start Redis server:
```bash
redis-server
```

2. Run the Django development server:
```bash
python manage.py runserver
```

3. Access the admin interface at `http://localhost:8000/admin/`

## API Endpoints

### Authentication
- POST `/api/auth/login/` - User login
- POST `/api/auth/logout/` - User logout
- GET `/api/auth/user/` - Get current user details

### Elections
- GET `/api/elections/` - List elections
- POST `/api/elections/` - Create election
- GET `/api/elections/{id}/` - Get election details
- POST `/api/elections/{id}/start/` - Start election
- POST `/api/elections/{id}/stop/` - Stop election
- GET `/api/elections/{id}/results/` - Get election results

### Positions
- GET `/api/elections/{election_id}/positions/` - List positions
- POST `/api/elections/{election_id}/positions/` - Create position

### Candidates
- GET `/api/elections/{election_id}/positions/{position_id}/candidates/` - List candidates
- POST `/api/elections/{election_id}/positions/{position_id}/candidates/` - Add candidate

### Voting
- POST `/api/votes/` - Cast a vote

### WebSocket
- WS `/ws/public/elections/{election_id}/live-results/` - Real-time election results

## Security Considerations

- All API endpoints (except public results) require authentication
- Role-based access control for admin and student users
- Secure password hashing
- CSRF protection
- Rate limiting on public endpoints
- Audit logging for all administrative actions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 