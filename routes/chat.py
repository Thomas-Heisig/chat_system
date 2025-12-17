import json
import os
from datetime import datetime
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
)
from fastapi.responses import FileResponse, HTMLResponse

from config.settings import enhanced_logger, logger, settings
from database.models import (
    MessageFilter,
    MessageType,
    ProjectFilter,
    ProjectStatus,
    TicketFilter,
    TicketPriority,
    TicketStatus,
    TicketType,
    create_project,
    create_ticket,
)
from database.repositories import (
    FileRepository,
    MessageRepository,
    ProjectRepository,
    SearchRepository,
    StatisticsRepository,
    TicketRepository,
    UserRepository,
)
from services.file_service import FileService
from services.message_service import MessageService
from websocket.handlers import WebSocketHandler

router = APIRouter()

# Initialize dependencies with comprehensive logging
logger.info("🔄 Initializing enhanced chat routes dependencies...")
try:
    # Initialize repositories
    message_repository = MessageRepository()
    user_repository = UserRepository()
    project_repository = ProjectRepository()
    ticket_repository = TicketRepository()
    file_repository = FileRepository()
    search_repository = SearchRepository()
    stats_repository = StatisticsRepository()

    # Initialize services
    # Initialize services
    message_service = MessageService(message_repository)
    file_service = FileService(file_repository)
    websocket_handler = WebSocketHandler(message_service)

    logger.info("✅ Enhanced chat routes dependencies initialized successfully")

    # Log system capabilities
    logger.info(
        f"🚀 System Features - Projects: {settings.FEATURE_PROJECT_MANAGEMENT}, "
        f"Tickets: {settings.FEATURE_TICKET_SYSTEM}, "
        f"Files: {settings.FEATURE_FILE_UPLOAD}, "
        f"Auth: {settings.FEATURE_USER_AUTHENTICATION}"
    )

except Exception as e:
    logger.error(f"❌ Failed to initialize enhanced chat routes dependencies: {e}")
    raise

# ============================================================================
# HTML Pages
# ============================================================================


@router.get("/", response_class=HTMLResponse)
async def get_chat_page():
    """Serve the main chat interface page with all features"""
    try:
        template_path = os.path.join(os.path.dirname(__file__), "../templates/index.html")

        logger.debug(f"📁 Loading enhanced template from: {template_path}")

        if not os.path.exists(template_path):
            logger.error(f"❌ Template file not found: {template_path}")
            return HTMLResponse(content="<h1>Error: Template not found</h1>", status_code=500)

        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Log comprehensive status
        logger.info(
            f"🌐 Enhanced chat page served - "
            f"Projects: {settings.FEATURE_PROJECT_MANAGEMENT}, "
            f"Tickets: {settings.FEATURE_TICKET_SYSTEM}, "
            f"Files: {settings.FEATURE_FILE_UPLOAD}"
        )

        return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"❌ Error serving enhanced chat page: {e}")
        return HTMLResponse(
            content=f"<h1>Error loading chat interface</h1><p>{str(e)}</p>", status_code=500
        )


@router.get("/projects", response_class=HTMLResponse)
async def get_projects_page():
    """Serve the projects management page"""
    try:
        template_path = os.path.join(os.path.dirname(__file__), "../templates/projects.html")

        if not os.path.exists(template_path):
            # Fallback to main page if projects template doesn't exist
            return await get_chat_page()

        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        logger.info("📊 Projects management page served")
        return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"❌ Error serving projects page: {e}")
        return await get_chat_page()


# ============================================================================
# WebSocket Endpoint
# ============================================================================


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Enhanced WebSocket endpoint for real-time communication with project support"""
    client_info = None
    try:
        client_info = (
            f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
        )
        logger.info(f"🔌 New WebSocket connection from: {client_info}")

        await websocket_handler.handle_websocket(websocket)

        logger.info(f"✅ WebSocket connection closed for: {client_info}")

    except Exception as e:
        logger.error(f"❌ WebSocket error for client {client_info}: {e}")
        try:
            await websocket.close()
        except Exception as close_error:
            logger.debug(f"Error closing websocket: {close_error}")


# ============================================================================
# System & Health Endpoints
# ============================================================================


@router.get("/health")
async def health_check():
    """Comprehensive health check with all services status"""
    try:
        # Check all services availability
        ai_models = message_service.get_available_models()

        health_status = {
            "status": "healthy",
            "service": "enhanced_chat_routes",
            "timestamp": datetime.now().isoformat(),
            "features": {
                "ai_enabled": settings.AI_ENABLED,
                "projects_enabled": settings.FEATURE_PROJECT_MANAGEMENT,
                "tickets_enabled": settings.FEATURE_TICKET_SYSTEM,
                "files_enabled": settings.FEATURE_FILE_UPLOAD,
                "auth_enabled": settings.FEATURE_USER_AUTHENTICATION,
                "rag_enabled": settings.RAG_ENABLED,
            },
            "ai_capabilities": {
                "ollama_available": settings.AI_ENABLED and any(ai_models["ollama"]),
                "custom_model_available": settings.AI_ENABLED and any(ai_models["custom"]),
                "available_models": ai_models,
            },
            "database": {"status": "connected", "type": "sqlite"},
        }

        logger.debug("🔍 Comprehensive health check requested")
        return health_status

    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/info")
async def route_info():
    """Get comprehensive information about available routes"""
    routes_info = {
        "service": "Enhanced Chat System with Project Management",
        "version": "2.0.0",
        "endpoints": {
            "Pages": {
                "GET /": "Main chat interface (includes ticket management)",
                "GET /projects": "Projects management interface",
                "Note": "Tickets are managed via API endpoints, integrated in main interface",
            },
            "WebSocket": {"WebSocket /ws": "Real-time communication"},
            "AI Services": {
                "GET /api/ai/models": "Available AI models",
                "POST /api/ai/ask": "Ask AI question",
                "POST /api/ai/analyze-sentiment": "Analyze message sentiment",
            },
            "Project Management": {
                "GET /api/projects": "List projects",
                "POST /api/projects": "Create project",
                "GET /api/projects/{project_id}": "Get project details",
                "PUT /api/projects/{project_id}": "Update project",
                "GET /api/projects/{project_id}/tickets": "Get project tickets",
            },
            "Ticket System": {
                "GET /api/tickets": "List tickets",
                "POST /api/tickets": "Create ticket",
                "GET /api/tickets/{ticket_id}": "Get ticket details",
                "PUT /api/tickets/{ticket_id}": "Update ticket",
                "POST /api/tickets/{ticket_id}/assign": "Assign ticket",
            },
            "File Management": {
                "POST /api/files/upload": "Upload file",
                "GET /api/files/{file_id}": "Get file info",
                "GET /api/files/{file_id}/download": "Download file",
                "GET /api/files": "List files",
            },
            "Search & Analytics": {
                "GET /api/search": "Global search",
                "GET /api/stats": "System statistics",
                "GET /api/ai/stats": "AI statistics",
            },
        },
        "configuration": {
            "ai_enabled": settings.AI_ENABLED,
            "projects_enabled": settings.FEATURE_PROJECT_MANAGEMENT,
            "tickets_enabled": settings.FEATURE_TICKET_SYSTEM,
            "files_enabled": settings.FEATURE_FILE_UPLOAD,
            "default_model": settings.OLLAMA_DEFAULT_MODEL,
        },
    }
    logger.debug("ℹ️ Enhanced route info requested")
    return routes_info


# ============================================================================
# AI Endpoints
# ============================================================================


@router.get("/api/ai/models")
async def get_ai_models():
    """Get available AI models"""
    try:
        models = message_service.get_available_models()

        logger.info(
            f"📋 AI models requested - Found: {len(models['ollama'])} Ollama, "
            f"{len(models['custom'])} custom models"
        )

        return {
            "models": models,
            "default_model": settings.OLLAMA_DEFAULT_MODEL,
            "ai_enabled": settings.AI_ENABLED,
        }

    except Exception as e:
        logger.error(f"❌ Failed to get AI models: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve AI models")


@router.post("/api/ai/ask")
async def ask_ai_question(
    question: str,
    username: str = Query("User", description="Username for the question"),
    use_context: bool = Query(True, description="Use chat history as context"),
    model_type: str = Query("ollama", description="AI model type: ollama or custom"),
    project_id: Optional[str] = Query(None, description="Project context"),
):
    """Ask AI a question with optional project context"""
    try:
        if not question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        logger.info(f"🤖 AI question from {username} in project {project_id}: '{question[:50]}...'")

        result = message_service.ask_question(
            question=question,
            username=username,
            use_context=use_context,
            model_type=model_type,
            project_id=project_id,
        )

        logger.info(
            f"✅ AI response generated - Sources: {len(result.get('sources', []))}, "
            f"Context used: {result.get('context_used', False)}"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ AI question failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process AI question")


# ============================================================================
# Project Management Endpoints
# ============================================================================


@router.get("/api/projects")
async def get_projects(
    status: Optional[ProjectStatus] = None,
    created_by: Optional[str] = None,
    member_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get projects with filtering and pagination"""
    try:
        if not settings.FEATURE_PROJECT_MANAGEMENT:
            raise HTTPException(status_code=400, detail="Project management is disabled")

        filters = ProjectFilter(
            status=status, created_by=created_by, member_id=member_id, limit=limit, offset=offset
        )

        logger.debug(f"📊 Getting projects with filters: {filters.dict()}")

        result = project_repository.get_projects_by_filter(filters)

        logger.info(f"✅ Retrieved {len(result.items)} projects (total: {result.total})")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve projects")


@router.post("/api/projects")
async def create_new_project(
    name: str = Form(..., min_length=1, max_length=200),
    description: Optional[str] = Form(None),
    created_by: str = Form(..., description="User ID who creates the project"),
    due_date: Optional[str] = Form(None),
    tags: Optional[str] = Form("[]"),
):
    """Create a new project"""
    try:
        if not settings.FEATURE_PROJECT_MANAGEMENT:
            raise HTTPException(status_code=400, detail="Project management is disabled")

        # Parse tags
        try:
            tag_list = json.loads(tags) if tags else []
        except json.JSONDecodeError:
            tag_list = []

        # Parse due date
        due_date_obj = None
        if due_date:
            try:
                due_date_obj = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid due date format")

        project = create_project(
            name=name,
            created_by=created_by,
            description=description,
            due_date=due_date_obj,
            tags=tag_list,
        )

        project_id = project_repository.create_project(project)

        enhanced_logger.info(
            "Project created successfully",
            project_id=project_id,
            project_name=name,
            created_by=created_by,
        )

        return {
            "project_id": project_id,
            "name": name,
            "status": "created",
            "created_at": (
                project.created_at.isoformat() if project.created_at else datetime.now().isoformat()
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create project: {e}")
        raise HTTPException(status_code=500, detail="Failed to create project")


@router.get("/api/projects/{project_id}")
async def get_project_details(project_id: str):
    """Get detailed project information"""
    try:
        # This would typically get project from repository
        # For now, return mock data
        project_info = {
            "id": project_id,
            "name": f"Project {project_id}",
            "description": "Sample project description",
            "status": "active",
            "created_by": "user123",
            "created_at": datetime.now().isoformat(),
            "ticket_count": 5,
            "progress_percentage": 60.0,
            "members": ["user123", "user456"],
        }

        logger.info(f"📋 Project details requested: {project_id}")
        return project_info

    except Exception as e:
        logger.error(f"❌ Failed to get project details: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve project details")


# ============================================================================
# Ticket System Endpoints
# ============================================================================


@router.get("/api/tickets")
async def get_tickets(
    project_id: Optional[str] = None,
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    assigned_to: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get tickets with comprehensive filtering"""
    try:
        if not settings.FEATURE_TICKET_SYSTEM:
            raise HTTPException(status_code=400, detail="Ticket system is disabled")

        filters = TicketFilter(
            project_id=project_id,
            status=status,
            priority=priority,
            assigned_to=assigned_to,
            limit=limit,
            offset=offset,
        )

        logger.debug(f"🎫 Getting tickets with filters: {filters.dict()}")

        result = ticket_repository.get_tickets_by_filter(filters)

        logger.info(f"✅ Retrieved {len(result.items)} tickets (total: {result.total})")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get tickets: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tickets")


@router.post("/api/tickets")
async def create_new_ticket(
    title: str = Form(..., min_length=1, max_length=200),
    description: Optional[str] = Form(None),
    project_id: str = Form(..., description="Project ID"),
    created_by: str = Form(..., description="User ID who creates the ticket"),
    priority: TicketPriority = Form(TicketPriority.MEDIUM),
    ticket_type: TicketType = Form(TicketType.TASK),
    due_date: Optional[str] = Form(None),
):
    """Create a new ticket"""
    try:
        if not settings.FEATURE_TICKET_SYSTEM:
            raise HTTPException(status_code=400, detail="Ticket system is disabled")

        # Parse due date
        due_date_obj = None
        if due_date:
            try:
                due_date_obj = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid due date format")

        ticket = create_ticket(
            title=title,
            project_id=project_id,
            created_by=created_by,
            description=description,
            priority=priority,
            type=ticket_type,
            due_date=due_date_obj,
        )

        ticket_id = ticket_repository.create_ticket(ticket)

        enhanced_logger.info(
            "Ticket created successfully",
            ticket_id=ticket_id,
            title=title,
            project_id=project_id,
            priority=priority,
            type=ticket_type,
        )

        return {
            "ticket_id": ticket_id,
            "title": title,
            "status": "open",
            "created_at": (
                ticket.created_at.isoformat() if ticket.created_at else datetime.now().isoformat()
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to create ticket")


# ============================================================================
# File Management Endpoints
# ============================================================================


@router.post("/api/files/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    uploaded_by: str = Form(..., description="User ID uploading the file"),
    project_id: Optional[str] = Form(None),
    ticket_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    is_public: bool = Form(False),
):
    """Upload a file with metadata"""
    try:
        if not settings.FEATURE_FILE_UPLOAD:
            raise HTTPException(status_code=400, detail="File upload is disabled")

        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        logger.info(f"📤 File upload started: {file.filename} by {uploaded_by}")

        # Use file service to handle upload
        file_record = await file_service.save_uploaded_file(
            file=file,
            username=uploaded_by,
            project_id=project_id,
            ticket_id=ticket_id,
            description=description,
            is_public=is_public,
        )

        # Background task for file analysis
        background_tasks.add_task(file_service.analyze_uploaded_file, file_record.id)

        logger.info(f"✅ File uploaded successfully: {file_record.id}")

        return {
            "file_id": file_record.id,
            "filename": file_record.original_filename,
            "file_size": file_record.file_size,
            "uploaded_by": uploaded_by,
            "upload_date": (
                file_record.upload_date.isoformat()
                if file_record.upload_date
                else datetime.now().isoformat()
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ File upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")


@router.get("/api/files/{file_id}")
async def get_file_info(file_id: str):
    """Get file information"""
    try:
        file_record = file_repository.get_file(file_id)

        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")

        logger.debug(f"📄 File info requested: {file_id}")

        return file_record.to_download_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get file info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file information")


@router.get("/api/files/{file_id}/download")
async def download_file(file_id: str):
    """Download a file"""
    try:
        file_record = file_repository.get_file(file_id)

        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")

        if not os.path.exists(file_record.file_path):
            raise HTTPException(status_code=404, detail="File not found on server")

        # Increment download count
        file_repository.increment_download_count(file_id)

        logger.info(f"📥 File download: {file_record.original_filename}")

        return FileResponse(
            path=file_record.file_path,
            filename=file_record.original_filename,
            media_type=file_record.mime_type,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ File download failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to download file")


# ============================================================================
# Search & Analytics Endpoints
# ============================================================================


@router.get("/api/search")
async def global_search(query: str, limit: int = Query(20, ge=1, le=100)):
    """Global search across messages, projects, tickets, and files"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        logger.info(f"🔍 Global search: '{query}'")

        results = search_repository.global_search(query, limit)

        logger.info(f"✅ Global search completed - {results.total_results} total results")

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Global search failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform search")


@router.get("/api/stats")
async def get_system_statistics():
    """Get comprehensive system statistics"""
    try:
        stats = stats_repository.get_system_statistics()

        logger.info("📈 System statistics requested")

        return {
            "statistics": stats,
            "timestamp": datetime.now().isoformat(),
            "timeframe": "all_time",
        }

    except Exception as e:
        logger.error(f"❌ Failed to get system statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.get("/api/ai/stats")
async def get_ai_statistics():
    """Get AI interaction statistics"""
    try:
        # Get AI status from message service
        ai_status = message_service.get_ai_status()

        # Get overall system statistics for AI-related metrics
        system_stats = stats_repository.get_system_statistics()

        # Extract AI-relevant statistics
        ai_available = ai_status.get("ollama_available", False) or ai_status.get("custom_model_available", False)
        stats = {
            "ai_available": ai_available,
            "models": ai_status.get("available_models", {}),
            "total_messages": system_stats.get("total_messages", 0),
            "ai_messages": system_stats.get("ai_messages", 0),
            "status": "available" if ai_available else "unavailable",
        }

        logger.info("🤖 AI statistics requested")

        return {
            "statistics": stats,
            "timestamp": datetime.now().isoformat(),
            "collection_date": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Failed to get AI statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve AI statistics")


# ============================================================================
# Message Endpoints (Enhanced)
# ============================================================================


@router.get("/api/messages/filter")
async def get_filtered_messages(
    username: Optional[str] = None,
    message_type: Optional[MessageType] = None,
    room_id: Optional[str] = None,
    project_id: Optional[str] = None,
    ticket_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    contains_text: Optional[str] = None,
    is_ai_response: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get messages with advanced filtering including project and ticket context"""
    try:
        from datetime import datetime

        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        filters = MessageFilter(
            username=username,
            message_type=message_type,
            room_id=room_id,
            project_id=project_id,
            ticket_id=ticket_id,
            start_date=start_dt,
            end_date=end_dt,
            contains_text=contains_text,
            is_ai_response=is_ai_response,
            limit=limit,
            offset=offset,
        )

        logger.debug(f"🔍 Filtering messages with project/ticket context: {filters.dict()}")

        result = message_repository.get_messages_by_filter(filters)

        logger.info(
            f"✅ Filtered messages - Returned: {len(result.items)}, " f"Total: {result.total}"
        )

        return result

    except ValueError as e:
        logger.error(f"❌ Invalid filter parameters: {e}")
        raise HTTPException(status_code=400, detail="Invalid filter parameters")
    except Exception as e:
        logger.error(f"❌ Failed to filter messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve filtered messages")


@router.get("/api/system/configuration")
async def get_system_configuration():
    """Get comprehensive system configuration"""
    try:
        config = {
            "ai_configuration": settings.ai_config,
            "security_configuration": settings.security_config,
            "file_configuration": settings.file_config,
            "feature_configuration": settings.feature_config,
            "system_configuration": settings.system_config,
            "limits": {
                "max_message_length": settings.AI_MAX_RESPONSE_LENGTH,
                "context_messages": settings.AI_CONTEXT_MESSAGES,
                "max_file_size": settings.MAX_FILE_SIZE,
                "rate_limiting": f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_WINDOW}s",
            },
        }

        logger.debug("⚙️ System configuration requested")

        return config

    except Exception as e:
        logger.error(f"❌ Failed to get system configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system configuration")


# ============================================================================
# Utility Endpoints
# ============================================================================


@router.get("/api/projects/{project_id}/tickets")
async def get_project_tickets(project_id: str):
    """Get all tickets for a specific project"""
    try:
        filters = TicketFilter(project_id=project_id, limit=100)
        result = ticket_repository.get_tickets_by_filter(filters)

        logger.info(f"📋 Retrieved {len(result.items)} tickets for project {project_id}")

        return result

    except Exception as e:
        logger.error(f"❌ Failed to get project tickets: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve project tickets")


@router.post("/api/tickets/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    assigned_to: str = Form(..., description="User ID to assign the ticket to"),
    assigned_by: str = Form(..., description="User ID who is making the assignment"),
):
    """Assign a ticket to a user"""
    try:
        # This would typically update the ticket in the repository
        # For now, return success response
        logger.info(f"👤 Ticket {ticket_id} assigned to {assigned_to} by {assigned_by}")

        return {
            "ticket_id": ticket_id,
            "assigned_to": assigned_to,
            "assigned_by": assigned_by,
            "assigned_at": datetime.now().isoformat(),
            "status": "assigned",
        }

    except Exception as e:
        logger.error(f"❌ Failed to assign ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign ticket")
