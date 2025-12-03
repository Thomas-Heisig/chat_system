# Chat System Setup Guide

This guide will help you set up and run the Chat System locally or with Docker.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Docker and Docker Compose (optional, for containerized deployment)
- Git

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Thomas-Heisig/chat_system.git
cd chat_system
```

### 2. Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` file to set your configuration. Key settings:

- `APP_ENVIRONMENT`: `development`, `production`, or `staging`
- `APP_SECRET_KEY`: Change this to a secure random string
- `DATABASE_TYPE`: `sqlite` (default), `postgresql`, or `mysql`
- `AI_ENABLED`: Enable/disable AI features
- `OLLAMA_BASE_URL`: URL for Ollama AI service (if using)

### 3. Local Development Setup

#### Option A: Using pip

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

The application will be available at `http://localhost:8000`

#### Option B: Using Make (recommended)

```bash
# Install dependencies
make install

# Run the application
make run

# Run tests
make test

# Run with coverage
make test-cov

# Format code
make format

# Check code quality
make lint
```

### 4. Docker Setup

#### Using Docker Compose (Recommended for Production)

```bash
# Start all services (app + postgres + redis + ollama)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The application will be available at `http://localhost:8000`

#### Using Docker only

```bash
# Build the image
docker build -t chat-system:latest .

# Run the container
docker run -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/logs:/app/logs \
  -e APP_ENVIRONMENT=production \
  chat-system:latest
```

## Development

### Project Structure

```
chat_system/
├── config/              # Configuration and settings
├── database/            # Database models and connection
├── routes/              # API routes and endpoints
├── services/            # Business logic services
├── websocket/           # WebSocket handlers
├── static/              # Static files (CSS, JS)
├── templates/           # HTML templates
├── tests/               # Test files
├── frontend/            # Frontend package configuration
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Python package configuration
├── Dockerfile           # Docker configuration
└── docker-compose.yml   # Multi-service Docker setup
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_message_service.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with black
black .

# Sort imports with isort
isort .

# Check code style with flake8
flake8 .

# Or use make commands
make format        # Format code
make format-check  # Check formatting without changes
make lint          # Run linting
```

## Features

- ✅ Real-time chat with WebSocket support
- ✅ AI integration (Ollama/OpenAI)
- ✅ RAG (Retrieval Augmented Generation) system
- ✅ Project and ticket management
- ✅ File upload and management
- ✅ User authentication (JWT)
- ✅ Admin dashboard
- ✅ Multi-database support (SQLite, PostgreSQL, MongoDB)
- ✅ Docker support

## Configuration

### Database

SQLite is used by default for development. For production, configure PostgreSQL:

```env
DATABASE_TYPE=postgresql
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=chat_system
DATABASE_USER=chatuser
DATABASE_PASSWORD=yourpassword
```

### AI Integration

Configure Ollama for local AI:

```env
AI_ENABLED=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama2
```

### RAG System

Enable RAG for document-based chat:

```env
RAG_ENABLED=true
VECTOR_DB_PROVIDER=chromadb
CHROMA_PERSIST_DIR=./chroma_data
```

## API Documentation

Once the application is running, access:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health Check: `http://localhost:8000/health`

## Troubleshooting

### Port already in use

If port 8000 is already in use, change it in `.env`:

```env
PORT=8080
```

### Database connection errors

Ensure your database is running and credentials are correct. For SQLite, check file permissions.

### Ollama not available

If you see "Ollama not available" warnings, either:
1. Install and start Ollama: `https://ollama.ai`
2. Disable AI features: `AI_ENABLED=false` in `.env`

### Import errors

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

## Security Notes

⚠️ **Important Security Steps:**

1. **Change the default admin password** immediately after first login
   - Default credentials: `admin` / `admin123`

2. **Set a strong APP_SECRET_KEY** in `.env`
   - Generate one: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

3. **Use HTTPS in production**
   - Configure SSL/TLS certificates
   - Update CORS settings for your domain

4. **Keep dependencies updated**
   - Regularly run: `pip install --upgrade -r requirements.txt`

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/Thomas-Heisig/chat_system/issues
- Documentation: See `README.md` and other docs in the repository

## License

See LICENSE file for details.
