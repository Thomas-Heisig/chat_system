# API Examples

Comprehensive examples for using the Universal Chat System API with multiple languages and tools.

## Table of Contents

- [Authentication](#authentication)
- [Messages](#messages)
- [RAG System](#rag-system)
- [Projects & Tickets](#projects--tickets)
- [Settings](#settings)
- [WebSocket](#websocket)
- [User Management](#user-management)
- [File Management](#file-management)

---

## Authentication

### Login (Get JWT Token)

**cURL:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your-password"
  }'
```

**Python:**
```python
import requests

url = "http://localhost:8000/api/auth/login"
data = {
    "username": "admin",
    "password": "your-password"
}

response = requests.post(url, json=data)
token_data = response.json()
token = token_data["access_token"]
print(f"Token: {token}")
```

**JavaScript (Node.js):**
```javascript
const axios = require('axios');

async function login() {
  const response = await axios.post('http://localhost:8000/api/auth/login', {
    username: 'admin',
    password: 'your-password'
  });
  
  const token = response.data.access_token;
  console.log('Token:', token);
  return token;
}
```

**JavaScript (Browser/Fetch):**
```javascript
async function login() {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      username: 'admin',
      password: 'your-password'
    })
  });
  
  const data = await response.json();
  return data.access_token;
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "username": "admin",
  "role": "admin"
}
```

### Register New User

**cURL:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "username": "newuser",
    "password": "securePassword123",
    "role": "user"
  }'
```

**Python:**
```python
headers = {"Authorization": f"Bearer {token}"}
data = {
    "username": "newuser",
    "password": "securePassword123",
    "role": "user"
}

response = requests.post(
    "http://localhost:8000/api/auth/register",
    headers=headers,
    json=data
)
print(response.json())
```

---

## Messages

### Get Messages

**cURL:**
```bash
# Get all messages
curl -X GET http://localhost:8000/api/messages \
  -H "Authorization: Bearer $TOKEN"

# Get messages with pagination
curl -X GET "http://localhost:8000/api/messages?skip=0&limit=50" \
  -H "Authorization: Bearer $TOKEN"

# Get messages for specific user
curl -X GET "http://localhost:8000/api/messages?username=admin" \
  -H "Authorization: Bearer $TOKEN"
```

**Python:**
```python
headers = {"Authorization": f"Bearer {token}"}

# Get all messages
response = requests.get(
    "http://localhost:8000/api/messages",
    headers=headers
)
messages = response.json()

# With pagination
params = {"skip": 0, "limit": 50}
response = requests.get(
    "http://localhost:8000/api/messages",
    headers=headers,
    params=params
)

# Filter by user
params = {"username": "admin"}
response = requests.get(
    "http://localhost:8000/api/messages",
    headers=headers,
    params=params
)
```

**JavaScript:**
```javascript
const token = await login();

// Get messages
const response = await axios.get('http://localhost:8000/api/messages', {
  headers: {
    'Authorization': `Bearer ${token}`
  },
  params: {
    skip: 0,
    limit: 50,
    username: 'admin'  // Optional filter
  }
});

const messages = response.data;
console.log('Messages:', messages);
```

### Send Message

**cURL:**
```bash
curl -X POST http://localhost:8000/api/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "message": "Hello from API!",
    "message_type": "user"
  }'
```

**Python:**
```python
headers = {"Authorization": f"Bearer {token}"}
data = {
    "username": "admin",
    "message": "Hello from API!",
    "message_type": "user"
}

response = requests.post(
    "http://localhost:8000/api/messages",
    headers=headers,
    json=data
)
print(response.json())
```

**JavaScript:**
```javascript
const message = await axios.post('http://localhost:8000/api/messages', {
  username: 'admin',
  message: 'Hello from API!',
  message_type: 'user'
}, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

console.log('Message sent:', message.data);
```

### Send Message to AI

**cURL:**
```bash
curl -X POST http://localhost:8000/api/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "message": "@ai What is the capital of France?",
    "message_type": "user"
  }'
```

**Python:**
```python
# Send message to AI
data = {
    "username": "admin",
    "message": "@ai What is the capital of France?",
    "message_type": "user"
}

response = requests.post(
    "http://localhost:8000/api/messages",
    headers=headers,
    json=data
)

# AI will respond automatically through WebSocket
print(response.json())
```

---

## RAG System

### Upload Document

**cURL:**
```bash
curl -X POST http://localhost:8000/api/rag/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"

# With metadata
curl -X POST http://localhost:8000/api/rag/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf" \
  -F 'metadata={"category":"technical","author":"John Doe"}'
```

**Python:**
```python
headers = {"Authorization": f"Bearer {token}"}

# Upload file
files = {"file": open("document.pdf", "rb")}
response = requests.post(
    "http://localhost:8000/api/rag/documents",
    headers=headers,
    files=files
)
print(response.json())

# With metadata
files = {"file": open("document.pdf", "rb")}
data = {
    "metadata": '{"category":"technical","author":"John Doe"}'
}
response = requests.post(
    "http://localhost:8000/api/rag/documents",
    headers=headers,
    files=files,
    data=data
)
```

**JavaScript (Node.js):**
```javascript
const FormData = require('form-data');
const fs = require('fs');

const form = new FormData();
form.append('file', fs.createReadStream('document.pdf'));

const response = await axios.post(
  'http://localhost:8000/api/rag/documents',
  form,
  {
    headers: {
      'Authorization': `Bearer ${token}`,
      ...form.getHeaders()
    }
  }
);

console.log('Upload result:', response.data);
```

### Query Documents (Semantic Search)

**cURL:**
```bash
curl -X POST http://localhost:8000/api/rag/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the system architecture?",
    "top_k": 5
  }'
```

**Python:**
```python
headers = {"Authorization": f"Bearer {token}"}
data = {
    "query": "What is the system architecture?",
    "top_k": 5
}

response = requests.post(
    "http://localhost:8000/api/rag/query",
    headers=headers,
    json=data
)

results = response.json()
for result in results["results"]:
    print(f"Document: {result['document']}")
    print(f"Content: {result['content']}")
    print(f"Similarity: {result['similarity']}")
    print("---")
```

**JavaScript:**
```javascript
const results = await axios.post('http://localhost:8000/api/rag/query', {
  query: 'What is the system architecture?',
  top_k: 5
}, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

results.data.results.forEach(result => {
  console.log('Document:', result.document);
  console.log('Content:', result.content);
  console.log('Similarity:', result.similarity);
});
```

### List Documents

**cURL:**
```bash
curl -X GET http://localhost:8000/api/rag/documents \
  -H "Authorization: Bearer $TOKEN"
```

**Python:**
```python
response = requests.get(
    "http://localhost:8000/api/rag/documents",
    headers=headers
)
documents = response.json()
print(f"Total documents: {len(documents)}")
```

### Delete Document

**cURL:**
```bash
curl -X DELETE http://localhost:8000/api/rag/documents/doc-id-123 \
  -H "Authorization: Bearer $TOKEN"
```

**Python:**
```python
doc_id = "doc-id-123"
response = requests.delete(
    f"http://localhost:8000/api/rag/documents/{doc_id}",
    headers=headers
)
print(response.json())
```

---

## Projects & Tickets

### Create Project

**cURL:**
```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Website Redesign",
    "description": "Complete redesign of company website",
    "status": "active"
  }'
```

**Python:**
```python
data = {
    "name": "Website Redesign",
    "description": "Complete redesign of company website",
    "status": "active"
}

response = requests.post(
    "http://localhost:8000/api/projects",
    headers=headers,
    json=data
)
project = response.json()
print(f"Created project: {project['id']}")
```

**JavaScript:**
```javascript
const project = await axios.post('http://localhost:8000/api/projects', {
  name: 'Website Redesign',
  description: 'Complete redesign of company website',
  status: 'active'
}, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

console.log('Project ID:', project.data.id);
```

### Create Ticket

**cURL:**
```bash
curl -X POST http://localhost:8000/api/projects/1/tickets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fix login button",
    "description": "Login button not working on mobile",
    "ticket_type": "bug",
    "priority": "high",
    "status": "open",
    "assigned_to": "developer1"
  }'
```

**Python:**
```python
project_id = 1
data = {
    "title": "Fix login button",
    "description": "Login button not working on mobile",
    "ticket_type": "bug",
    "priority": "high",
    "status": "open",
    "assigned_to": "developer1"
}

response = requests.post(
    f"http://localhost:8000/api/projects/{project_id}/tickets",
    headers=headers,
    json=data
)
ticket = response.json()
print(f"Created ticket: {ticket['id']}")
```

### Get Project Tickets

**cURL:**
```bash
# All tickets
curl -X GET http://localhost:8000/api/projects/1/tickets \
  -H "Authorization: Bearer $TOKEN"

# Filter by status
curl -X GET "http://localhost:8000/api/projects/1/tickets?status=open" \
  -H "Authorization: Bearer $TOKEN"

# Filter by priority
curl -X GET "http://localhost:8000/api/projects/1/tickets?priority=high" \
  -H "Authorization: Bearer $TOKEN"
```

**Python:**
```python
# Get all tickets
response = requests.get(
    f"http://localhost:8000/api/projects/{project_id}/tickets",
    headers=headers
)

# Filter by status
params = {"status": "open"}
response = requests.get(
    f"http://localhost:8000/api/projects/{project_id}/tickets",
    headers=headers,
    params=params
)

# Filter by assigned user
params = {"assigned_to": "developer1"}
response = requests.get(
    f"http://localhost:8000/api/projects/{project_id}/tickets",
    headers=headers,
    params=params
)
```

### Update Ticket Status

**cURL:**
```bash
curl -X PATCH http://localhost:8000/api/projects/1/tickets/5 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress"
  }'
```

**Python:**
```python
ticket_id = 5
data = {"status": "in_progress"}

response = requests.patch(
    f"http://localhost:8000/api/projects/{project_id}/tickets/{ticket_id}",
    headers=headers,
    json=data
)
print(response.json())
```

---

## Settings

### Get Settings

**cURL:**
```bash
curl -X GET http://localhost:8000/api/settings \
  -H "Authorization: Bearer $TOKEN"
```

**Python:**
```python
response = requests.get(
    "http://localhost:8000/api/settings",
    headers=headers
)
settings = response.json()
print(f"AI Enabled: {settings['ai_enabled']}")
print(f"RAG Enabled: {settings['rag_enabled']}")
```

### Update Settings

**cURL:**
```bash
curl -X PUT http://localhost:8000/api/settings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_enabled": true,
    "rag_enabled": true,
    "max_message_length": 10000
  }'
```

**Python:**
```python
data = {
    "ai_enabled": True,
    "rag_enabled": True,
    "max_message_length": 10000
}

response = requests.put(
    "http://localhost:8000/api/settings",
    headers=headers,
    json=data
)
print(response.json())
```

---

## WebSocket

### Connect to WebSocket

**JavaScript (Browser):**
```javascript
// Get token first
const token = await login();

// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected to WebSocket');
  
  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    token: token
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
  
  if (data.type === 'message') {
    console.log(`${data.username}: ${data.message}`);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from WebSocket');
};
```

**Python (websockets library):**
```python
import asyncio
import websockets
import json

async def connect_websocket():
    # Get token
    token = login()  # Use login function from above
    
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # Authenticate
        await websocket.send(json.dumps({
            'type': 'auth',
            'token': token
        }))
        
        # Send message
        await websocket.send(json.dumps({
            'type': 'message',
            'username': 'admin',
            'message': 'Hello from Python!'
        }))
        
        # Receive messages
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {data}")

asyncio.run(connect_websocket())
```

### Send Message via WebSocket

**JavaScript:**
```javascript
// Send chat message
ws.send(JSON.stringify({
  type: 'message',
  username: 'admin',
  message: 'Hello everyone!'
}));

// Send typing indicator
ws.send(JSON.stringify({
  type: 'typing',
  username: 'admin',
  is_typing: true
}));
```

---

## User Management

### List Users

**cURL:**
```bash
curl -X GET http://localhost:8000/api/users \
  -H "Authorization: Bearer $TOKEN"
```

**Python:**
```python
response = requests.get(
    "http://localhost:8000/api/users",
    headers=headers
)
users = response.json()
for user in users:
    print(f"{user['username']} - {user['role']}")
```

### Update User Role

**cURL:**
```bash
curl -X PATCH http://localhost:8000/api/users/5 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "moderator"
  }'
```

**Python:**
```python
user_id = 5
data = {"role": "moderator"}

response = requests.patch(
    f"http://localhost:8000/api/users/{user_id}",
    headers=headers,
    json=data
)
print(response.json())
```

---

## File Management

### Upload File

**cURL:**
```bash
curl -X POST http://localhost:8000/api/files/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@image.png" \
  -F "username=admin"
```

**Python:**
```python
files = {"file": open("image.png", "rb")}
data = {"username": "admin"}

response = requests.post(
    "http://localhost:8000/api/files/upload",
    headers=headers,
    files=files,
    data=data
)
file_info = response.json()
print(f"File URL: {file_info['url']}")
```

### List Files

**cURL:**
```bash
curl -X GET http://localhost:8000/api/files \
  -H "Authorization: Bearer $TOKEN"
```

**Python:**
```python
response = requests.get(
    "http://localhost:8000/api/files",
    headers=headers
)
files = response.json()
```

---

## Complete Python Example

```python
import requests
import time

class ChatSystemClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.headers = {}
    
    def login(self, username, password):
        """Login and store token"""
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"username": username, "password": password}
        )
        data = response.json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        return data
    
    def send_message(self, username, message):
        """Send a chat message"""
        return requests.post(
            f"{self.base_url}/api/messages",
            headers=self.headers,
            json={"username": username, "message": message}
        ).json()
    
    def get_messages(self, skip=0, limit=50):
        """Get messages with pagination"""
        return requests.get(
            f"{self.base_url}/api/messages",
            headers=self.headers,
            params={"skip": skip, "limit": limit}
        ).json()
    
    def upload_document(self, file_path):
        """Upload document to RAG system"""
        with open(file_path, "rb") as f:
            files = {"file": f}
            return requests.post(
                f"{self.base_url}/api/rag/documents",
                headers=self.headers,
                files=files
            ).json()
    
    def query_rag(self, query, top_k=5):
        """Query RAG system"""
        return requests.post(
            f"{self.base_url}/api/rag/query",
            headers=self.headers,
            json={"query": query, "top_k": top_k}
        ).json()
    
    def create_project(self, name, description):
        """Create a new project"""
        return requests.post(
            f"{self.base_url}/api/projects",
            headers=self.headers,
            json={"name": name, "description": description}
        ).json()

# Usage
if __name__ == "__main__":
    client = ChatSystemClient()
    
    # Login
    client.login("admin", "your-password")
    print("Logged in successfully")
    
    # Send message
    result = client.send_message("admin", "Hello from Python client!")
    print(f"Message sent: {result}")
    
    # Get messages
    messages = client.get_messages(limit=10)
    print(f"Retrieved {len(messages)} messages")
    
    # Upload document (if file exists)
    # result = client.upload_document("document.pdf")
    # print(f"Document uploaded: {result}")
    
    # Query RAG
    # results = client.query_rag("What is the architecture?")
    # print(f"Found {len(results['results'])} results")
```

---

## Complete JavaScript Example

```javascript
const axios = require('axios');

class ChatSystemClient {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.token = null;
  }

  async login(username, password) {
    const response = await axios.post(`${this.baseURL}/api/auth/login`, {
      username,
      password
    });
    this.token = response.data.access_token;
    return response.data;
  }

  getHeaders() {
    return {
      'Authorization': `Bearer ${this.token}`
    };
  }

  async sendMessage(username, message) {
    const response = await axios.post(
      `${this.baseURL}/api/messages`,
      { username, message },
      { headers: this.getHeaders() }
    );
    return response.data;
  }

  async getMessages(skip = 0, limit = 50) {
    const response = await axios.get(
      `${this.baseURL}/api/messages`,
      {
        headers: this.getHeaders(),
        params: { skip, limit }
      }
    );
    return response.data;
  }

  async uploadDocument(filePath) {
    const FormData = require('form-data');
    const fs = require('fs');
    
    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));
    
    const response = await axios.post(
      `${this.baseURL}/api/rag/documents`,
      form,
      {
        headers: {
          ...this.getHeaders(),
          ...form.getHeaders()
        }
      }
    );
    return response.data;
  }

  async queryRAG(query, topK = 5) {
    const response = await axios.post(
      `${this.baseURL}/api/rag/query`,
      { query, top_k: topK },
      { headers: this.getHeaders() }
    );
    return response.data;
  }

  async createProject(name, description) {
    const response = await axios.post(
      `${this.baseURL}/api/projects`,
      { name, description },
      { headers: this.getHeaders() }
    );
    return response.data;
  }
}

// Usage
async function main() {
  const client = new ChatSystemClient();
  
  // Login
  await client.login('admin', 'your-password');
  console.log('Logged in successfully');
  
  // Send message
  const result = await client.sendMessage('admin', 'Hello from Node.js!');
  console.log('Message sent:', result);
  
  // Get messages
  const messages = await client.getMessages(0, 10);
  console.log(`Retrieved ${messages.length} messages`);
  
  // Create project
  const project = await client.createProject(
    'New Project',
    'Project description'
  );
  console.log('Project created:', project);
}

main().catch(console.error);
```

---

## Error Handling

### Common Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden:**
```json
{
  "detail": "Not enough permissions"
}
```

**404 Not Found:**
```json
{
  "detail": "Resource not found"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Python Error Handling

```python
try:
    response = requests.post(
        "http://localhost:8000/api/messages",
        headers=headers,
        json=data,
        timeout=10
    )
    response.raise_for_status()  # Raise exception for 4xx/5xx
    return response.json()
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e.response.status_code}")
    print(f"Details: {e.response.json()}")
except requests.exceptions.Timeout:
    print("Request timed out")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

### JavaScript Error Handling

```javascript
try {
  const response = await axios.post(
    'http://localhost:8000/api/messages',
    data,
    { headers, timeout: 10000 }
  );
  return response.data;
} catch (error) {
  if (error.response) {
    // Server responded with error status
    console.error('Error status:', error.response.status);
    console.error('Error data:', error.response.data);
  } else if (error.request) {
    // Request made but no response
    console.error('No response received');
  } else {
    // Error setting up request
    console.error('Request setup error:', error.message);
  }
}
```

---

**Last Updated:** 2025-12-06

For more information, see the [API Documentation](API.md) and [Troubleshooting Guide](TROUBLESHOOTING.md).
