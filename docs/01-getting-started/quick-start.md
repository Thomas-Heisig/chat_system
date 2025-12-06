# Quick Start Guide

Get the Universal Chat System up and running in just 5 minutes!

## Prerequisites

Before you begin, ensure you have:
- **Python 3.9+** installed
- **pip** package manager
- **Git** for version control

## 🚀 Quick Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Thomas-Heisig/chat_system.git
cd chat_system
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# The default settings work for quick start
# You can edit .env later for customization
```

### 5. Run the Application

```bash
python main.py
```

The application will start at **http://localhost:8000**

### 6. Access the System

1. Open your browser and navigate to: **http://localhost:8000**
2. Login with default credentials:
   - **Username**: `admin`
   - **Password**: `admin123`
3. ⚠️ **IMPORTANT**: You will be prompted to change the password on first login

## 📱 First Steps

### Explore the Interface

The admin dashboard has multiple tabs:

- **Chat**: Send messages and interact with AI
- **Projects**: Create and manage projects
- **Files**: Upload and manage documents
- **Settings**: Configure system settings
- **RAG System**: Upload documents for AI context

### Send Your First Message

1. Click on the **Chat** tab
2. Type a message in the input field
3. Press Enter or click Send
4. The system will respond (AI features require Ollama setup)

### Create Your First Project

1. Click on the **Projects** tab
2. Click **Create Project**
3. Fill in project details
4. Click Save

## 🎯 What's Next?

### Configure AI Features

To enable AI responses:

1. Install Ollama: https://ollama.ai/
2. Pull a model: `ollama pull llama2`
3. The system will automatically connect to Ollama

### Upload Documents for RAG

1. Click on the **RAG System** tab
2. Upload documents (PDF, DOCX, TXT, MD)
3. Documents are automatically processed for semantic search
4. Ask questions about your documents in the chat

### Explore API Documentation

Visit **http://localhost:8000/docs** for interactive API documentation

## 🐳 Docker Quick Start

Prefer Docker? Use this one-liner:

```bash
docker-compose up -d
```

This starts:
- Chat System application
- PostgreSQL database
- Redis cache
- Ollama AI service
- ChromaDB vector database

## 🔧 Quick Configuration

### Essential Environment Variables

Edit `.env` file:

```bash
# Application
APP_NAME="Universal Chat System"
APP_ENVIRONMENT=development
APP_DEBUG=true

# Database (default SQLite is fine for quick start)
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./chat.db

# AI Features (optional)
AI_ENABLED=true
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Security (change in production!)
APP_SECRET_KEY=change-this-secret-key-in-production
JWT_SECRET_KEY=change-this-jwt-secret-key-in-production
```

## ❓ Troubleshooting

### Application won't start

```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Can't login

- Default credentials: `admin` / `admin123`
- Check the console for any error messages
- Ensure database is initialized (happens automatically)

### Port 8000 already in use

Change the port in `.env`:
```bash
PORT=8080
```

### AI responses not working

1. Check if Ollama is running: `curl http://localhost:11434`
2. Pull a model: `ollama pull llama2`
3. Set `AI_ENABLED=true` in `.env`

## 📚 Further Reading

- **[Installation Guide](installation.md)** - Detailed installation options
- **[Configuration Guide](configuration.md)** - Complete configuration reference
- **[User Guide](../02-user-guide/README.md)** - How to use the system
- **[Troubleshooting](../06-operations/troubleshooting.md)** - Common issues

## 🆘 Getting Help

- **Documentation**: [Complete Docs](../README.md)
- **Issues**: [GitHub Issues](https://github.com/Thomas-Heisig/chat_system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Thomas-Heisig/chat_system/discussions)

---

**Version:** 2.0.0  
**Last Updated:** 2025-12-06  
**Language:** English | [Deutsch](quick-start.de.md)
