# Frontend API Guide for College Election Portal

## Quick Start for React Developers

### Base URL
```
https://gttech.pythonanywhere.com
```

### Authentication
All API calls (except results) require JWT authentication.

#### 1. Login
```javascript
const login = async (username, password) => {
  const response = await fetch('https://gttech.pythonanywhere.com/auth/login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  });
  
  const data = await response.json();
  if (response.ok) {
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    return data.user;
  } else {
    throw new Error(data.error || 'Login failed');
  }
};
```

#### 2. API Helper with Authentication
```javascript
const apiCall = async (endpoint, options = {}) => {
  const token = localStorage.getItem('access_token');
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    },
    ...options,
  };
  
  const response = await fetch(`https://gttech.pythonanywhere.com${endpoint}`, config);
  
  if (response.status === 401) {
    // Token expired, try to refresh
    const refreshed = await refreshToken();
    if (refreshed) {
      return apiCall(endpoint, options); // Retry with new token
    }
  }
  
  return response.json();
};
```

## Core Endpoints

### 1. List Public Elections (Public - No Auth Required)
```javascript
// GET /elections/
const getPublicElections = async () => {
  const response = await fetch('https://gttech.pythonanywhere.com/elections/');
  return response.json();
};

// Example usage
const elections = await getPublicElections();
console.log(elections);
// Response:
// [
//   {
//     "id": 1,
//     "title": "Student Council Election 2024",
//     "description": "Annual student council election",
//     "status": "active",
//     "start_datetime": "2024-03-01T09:00:00Z",
//     "end_datetime": "2024-03-01T17:00:00Z",
//     "positions": [
//       {
//         "position_id": 1,
//         "position_title": "President",
//         "candidates": [
//           {
//             "candidate_id": 1,
//             "candidate_name": "John Doe",
//             "vote_count": 45
//           },
//           {
//             "candidate_id": 2,
//             "candidate_name": "Jane Smith",
//             "vote_count": 38
//           }
//         ]
//       },
//       {
//         "position_id": 2,
//         "position_title": "Vice President",
//         "candidates": [
//           {
//             "candidate_id": 3,
//             "candidate_name": "Mike Johnson",
//             "vote_count": 52
//           },
//           {
//             "candidate_id": 4,
//             "candidate_name": "Sarah Wilson",
//             "vote_count": 31
//           }
//         ]
//       }
//     ]
//   },
//   {
//     "id": 2,
//     "title": "Class Representative Election 2024",
//     "description": "Class representative election",
//     "status": "completed",
//     "start_datetime": "2024-02-15T09:00:00Z",
//     "end_datetime": "2024-02-15T17:00:00Z",
//     "positions": [...]
//   }
// ]
```

### 2. Get Election Results (Public - No Auth Required)
```javascript
// GET /elections/{election_id}/results/
const getElectionResults = async (electionId) => {
  const response = await fetch(`https://gttech.pythonanywhere.com/elections/${electionId}/results/`);
  return response.json();
};

// Example usage
const results = await getElectionResults(1);
console.log(results);
// Response:
// {
//   "id": 1,
//   "title": "Student Council Election 2024",
//   "positions": [
//     {
//       "position_id": 1,
//       "position_title": "President",
//       "candidates": [
//         {
//           "candidate_id": 1,
//           "candidate_name": "John Doe",
//           "vote_count": 45
//         },
//         {
//           "candidate_id": 2,
//           "candidate_name": "Jane Smith",
//           "vote_count": 38
//         }
//       ]
//     }
//   ]
// }
```

### 3. List Elections
```javascript
// GET /api/elections/
const getElections = async () => {
  return await apiCall('/api/elections/');
};
```

### 4. Get Election Details
```javascript
// GET /api/elections/{id}/
const getElectionDetails = async (electionId) => {
  return await apiCall(`/api/elections/${electionId}/`);
};
```

### 5. Cast a Vote
```javascript
// POST /api/votes/
const castVote = async (electionId, positionId, candidateId) => {
  return await apiCall('/api/votes/', {
    method: 'POST',
    body: JSON.stringify({
      election: electionId,
      position: positionId,
      candidate: candidateId,
    }),
  });
};
```

### 6. Get User's Votes
```javascript
// GET /api/votes/
const getUserVotes = async () => {
  return await apiCall('/api/votes/');
};
```

## Real-time Updates with WebSocket

### WebSocket Connection
```javascript
const connectToLiveResults = (electionId, onUpdate) => {
  const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
  const ws_path = `${ws_scheme}://gttech.pythonanywhere.com/ws/public/elections/${electionId}/live-results/`;
  
  const socket = new WebSocket(ws_path);
  
  socket.onopen = () => {
    console.log('Connected to live results');
  };
  
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onUpdate(data);
  };
  
  socket.onclose = () => {
    console.log('Disconnected from live results');
  };
  
  socket.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  
  return socket;
};

// Example usage
const socket = connectToLiveResults(1, (results) => {
  console.log('Live results updated:', results);
  // Update your React state here
});
```

## React Hook Examples

### Custom Hook for Election Results
```javascript
import { useState, useEffect } from 'react';

const useElectionResults = (electionId) => {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true);
        const data = await getElectionResults(electionId);
        setResults(data);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [electionId]);

  return { results, loading, error };
};
```

### Custom Hook for Live Results
```javascript
import { useState, useEffect, useRef } from 'react';

const useLiveResults = (electionId) => {
  const [results, setResults] = useState(null);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    // Get initial results
    getElectionResults(electionId).then(setResults);

    // Connect to WebSocket
    socketRef.current = connectToLiveResults(electionId, (data) => {
      setResults(data);
    });

    setConnected(true);

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [electionId]);

  return { results, connected };
};
```

## Error Handling

### Common Error Responses
```javascript
// 400 Bad Request
{
  "error": "Results are only available for active or completed elections"
}

// 401 Unauthorized
{
  "detail": "Authentication credentials were not provided."
}

// 403 Forbidden
{
  "detail": "You do not have permission to perform this action."
}

// 404 Not Found
{
  "detail": "Election not found."
}
```

### Error Handling Helper
```javascript
const handleApiError = (error) => {
  if (error.status === 401) {
    // Redirect to login
    window.location.href = '/login';
  } else if (error.status === 403) {
    // Show permission denied message
    alert('You do not have permission to perform this action');
  } else if (error.status === 404) {
    // Show not found message
    alert('The requested resource was not found');
  } else {
    // Show generic error
    alert('An error occurred. Please try again.');
  }
};
```

## Complete React Component Example

### Public Election Results Viewer
```javascript
import React, { useState, useEffect } from 'react';

const PublicElectionResults = () => {
  const [elections, setElections] = useState([]);
  const [selectedElection, setSelectedElection] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch available elections
  useEffect(() => {
    const fetchElections = async () => {
      try {
        const response = await fetch('https://gttech.pythonanywhere.com/elections/');
        const data = await response.json();
        setElections(data);
        
        // Auto-select the first active election
        const activeElection = data.find(e => e.status === 'active');
        if (activeElection) {
          setSelectedElection(activeElection);
        }
      } catch (err) {
        setError('Failed to load elections');
      } finally {
        setLoading(false);
      }
    };

    fetchElections();
  }, []);

  // Fetch results when election is selected
  useEffect(() => {
    if (!selectedElection) return;

    const fetchResults = async () => {
      try {
        const response = await fetch(`https://gttech.pythonanywhere.com/elections/${selectedElection.id}/results/`);
        const data = await response.json();
        setResults(data);
      } catch (err) {
        setError('Failed to load results');
      }
    };

    fetchResults();

    // Connect to live updates
    const socket = connectToLiveResults(selectedElection.id, (data) => {
      setResults(data);
    });

    return () => socket.close();
  }, [selectedElection]);

  if (loading) return <div>Loading elections...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Live Election Results</h2>
      
      {/* Election Selector */}
      <div className="election-selector">
        <label>Select Election: </label>
        <select 
          value={selectedElection?.id || ''} 
          onChange={(e) => {
            const election = elections.find(el => el.id === parseInt(e.target.value));
            setSelectedElection(election);
          }}
        >
          <option value="">Choose an election...</option>
          {elections.map(election => (
            <option key={election.id} value={election.id}>
              {election.title} ({election.status})
            </option>
          ))}
        </select>
      </div>

      {/* Results Display */}
      {selectedElection && results && (
        <div>
          <h3>{results.title} - Live Results</h3>
          <div className="status-badge">
            Status: {selectedElection.status}
          </div>
          
          {results.positions.map((position) => (
            <div key={position.position_id} className="position-results">
              <h4>{position.position_title}</h4>
              {position.candidates.map((candidate) => (
                <div key={candidate.candidate_id} className="candidate-result">
                  <span className="candidate-name">{candidate.candidate_name}</span>
                  <span className="vote-count">{candidate.vote_count} votes</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PublicElectionResults;
```

### Election Results Component
```javascript
import React, { useState, useEffect } from 'react';

const ElectionResults = ({ electionId }) => {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true);
        const data = await getElectionResults(electionId);
        setResults(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchResults();

    // Connect to live updates
    const socket = connectToLiveResults(electionId, (data) => {
      setResults(data);
    });

    return () => socket.close();
  }, [electionId]);

  if (loading) return <div>Loading results...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!results) return <div>No results available</div>;

  return (
    <div>
      <h2>{results.title} - Live Results</h2>
      {results.positions.map((position) => (
        <div key={position.position_id}>
          <h3>{position.position_title}</h3>
          {position.candidates.map((candidate) => (
            <div key={candidate.candidate_id}>
              <span>{candidate.candidate_name}</span>
              <span>{candidate.vote_count} votes</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

export default ElectionResults;
```

## Testing the API

### Using Swagger UI
1. Visit: `https://gttech.pythonanywhere.com/api/docs/`
2. Click "Authorize" and enter your JWT token
3. Test endpoints directly from the browser

### Using curl
```bash
# Get election results (no auth required)
curl https://gttech.pythonanywhere.com/elections/1/results/

# Login and get token
curl -X POST https://gttech.pythonanywhere.com/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Use token for authenticated requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://gttech.pythonanywhere.com/api/elections/
```

## Notes for Frontend Developers

1. **CORS**: The API supports CORS for cross-origin requests
2. **Authentication**: Use JWT Bearer tokens in the Authorization header
3. **Real-time**: Use WebSocket for live updates, REST API for initial data
4. **Error Handling**: Always check response status and handle errors gracefully
5. **Token Refresh**: Implement automatic token refresh when 401 errors occur
6. **Public Endpoints**: Results endpoint doesn't require authentication
7. **Rate Limiting**: Be mindful of API rate limits in production

## Support

If you encounter issues:
1. Check the Swagger documentation at `/api/docs/`
2. Verify your authentication token is valid
3. Check the browser console for WebSocket connection errors
4. Ensure the election ID exists and is active/completed 