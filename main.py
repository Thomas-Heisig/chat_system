import os
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from contextlib import asynccontextmanager
from pathlib import Path

from config.settings import settings, logger, enhanced_logger
from database.connection import init_database, get_database_stats, check_database_health
from routes.chat import router as chat_router
from routes.messages import router as messages_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Enhanced lifespan manager for startup and shutdown events"""
    startup_time = time.time()
    
    # Startup
    enhanced_logger.info(
        "Starting Chat System Application",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENVIRONMENT
    )
    
    try:
        # Initialize database
        enhanced_logger.info("Initializing database")
        init_database()
        
        # Verify database health
        db_health = check_database_health()
        enhanced_logger.info(
            "Database initialized",
            status=db_health.get('status', 'unknown'),
            version=db_health.get('version', 'unknown')
        )
        
        # Log system configuration
        enhanced_logger.info(
            "System configuration",
            features={
                "ai_enabled": settings.AI_ENABLED,
                "projects_enabled": settings.FEATURE_PROJECT_MANAGEMENT,
                "tickets_enabled": settings.FEATURE_TICKET_SYSTEM,
                "files_enabled": settings.FEATURE_FILE_UPLOAD,
                "auth_enabled": settings.FEATURE_USER_AUTHENTICATION,
                "websocket_enabled": settings.WEBSOCKET_ENABLED
            },
            security={
                "rate_limiting": settings.RATE_LIMIT_ENABLED,
                "cors_origins_count": len(settings.CORS_ORIGINS)
            }
        )
        
    except Exception as e:
        enhanced_logger.error(
            "Startup failed",
            error=str(e),
            error_type=type(e).__name__
        )
        raise
    
    startup_duration = (time.time() - startup_time) * 1000
    enhanced_logger.info(
        "Application started successfully",
        startup_time_ms=startup_duration,
        total_services=5  # Database, AI, Projects, Tickets, Files
    )
    
    yield  # Application runs here
    
    # Shutdown
    shutdown_start = time.time()
    enhanced_logger.info("Shutting down Chat System")
    
    try:
        # Perform cleanup tasks
        enhanced_logger.info("Performing cleanup tasks")
        
        # Log final statistics
        db_stats = get_database_stats()
        enhanced_logger.info(
            "Final database statistics",
            total_messages=db_stats.get('messages_count', 0),
            total_projects=db_stats.get('projects_count', 0),
            total_tickets=db_stats.get('tickets_count', 0),
            total_files=db_stats.get('files_count', 0)
        )
        
    except Exception as e:
        enhanced_logger.error("Error during shutdown", error=str(e))
    
    shutdown_duration = (time.time() - shutdown_start) * 1000
    enhanced_logger.info(
        "Shutdown completed",
        shutdown_time_ms=shutdown_duration
    )

# Create FastAPI application with enhanced configuration
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    🚀 Enhanced Chat System with AI, Project Management, and Real-time Collaboration
    
    ## Features
    
    - 💬 Real-time chat with WebSocket support
    - 🤖 AI-powered responses and analysis
    - 📊 Project management and ticket system
    - 📁 File upload and management
    - 🔍 Advanced search and analytics
    - 👥 User management and authentication
    - 📱 Responsive web interface
    
    ## API Endpoints
    
    - **Chat**: WebSocket and REST endpoints for messaging
    - **Projects**: Complete project management system
    - **Tickets**: Issue tracking and task management
    - **Files**: Secure file upload and management
    - **AI**: Artificial intelligence services
    - **Analytics**: System statistics and insights
    """,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.APP_DEBUG else None,
    redoc_url="/redoc" if settings.APP_DEBUG else None,
    openapi_url="/openapi.json" if settings.APP_DEBUG else None,
    lifespan=lifespan,
    contact={
        "name": "Chat System Support",
        "url": "https://github.com/your-repo/chat-system",
        "email": "support@chatsystem.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# Enhanced CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    expose_headers=settings.CORS_EXPOSE_HEADERS,
)

# Enhanced logging middleware with performance monitoring
@app.middleware("http")
async def enhanced_logging_middleware(request: Request, call_next):
    start_time = time.time()
    request_id = str(int(start_time * 1000))
    
    # Log request details
    enhanced_logger.info(
        "Request started",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        client_host=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown")
    )
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        # Log response details
        enhanced_logger.info(
            "Request completed",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time_ms=process_time,
            response_size=response.headers.get("content-length", "unknown")
        )
        
        # Add performance headers
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        enhanced_logger.error(
            "Request failed",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            error=str(e),
            error_type=type(e).__name__,
            process_time_ms=process_time
        )
        raise

# Security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Add security headers
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }
    
    for header, value in security_headers.items():
        response.headers[header] = value
        
    return response

# Enhanced exception handlers
@app.exception_handler(HTTPException)
async def enhanced_http_exception_handler(request: Request, exc: HTTPException):
    enhanced_logger.warning(
        "HTTP Exception",
        status_code=exc.status_code,
        detail=exc.detail,
        method=request.method,
        url=str(request.url),
        client_host=request.client.host if request.client else "unknown"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "timestamp": time.time()
        },
        headers={"X-Error-Type": "HTTPException"}
    )

@app.exception_handler(Exception)
async def enhanced_global_exception_handler(request: Request, exc: Exception):
    enhanced_logger.error(
        "Unhandled Exception",
        error=str(exc),
        error_type=type(exc).__name__,
        method=request.method,
        url=str(request.url),
        client_host=request.client.host if request.client else "unknown",
        stack_trace=str(exc.__traceback__) if settings.APP_DEBUG else "hidden"
    )
    
    error_detail = str(exc) if settings.APP_DEBUG else "Internal server error"
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": error_detail,
            "status_code": 500,
            "path": request.url.path,
            "method": request.method,
            "timestamp": time.time()
        },
        headers={"X-Error-Type": "InternalServerError"}
    )

# Static Files with enhanced configuration
static_dirs = [
    ("/static", "static", "Static files (CSS, JS, images)"),
    ("/uploads", "uploads", "Uploaded user files"),
    ("/docs", "docs", "Documentation files")
]

for route, directory, description in static_dirs:
    if Path(directory).exists():
        app.mount(route, StaticFiles(directory=directory), name=description)
        enhanced_logger.info(f"Static directory mounted", route=route, directory=directory)
    else:
        enhanced_logger.warning(f"Static directory not found", directory=directory)

# Register routes with enhanced logging
routes_config = [
    (chat_router, "", "Chat routes (WebSocket, UI, AI)"),
    (messages_router, "/api", "Messages API routes")
]

for router, prefix, description in routes_config:
    app.include_router(router, prefix=prefix, tags=[description.split(' ')[0].lower()])
    enhanced_logger.info(f"Router registered", prefix=prefix, description=description)

# Enhanced health and info endpoints
@app.get("/health", tags=["monitoring"])
async def comprehensive_health_check():
    """Comprehensive health check with system status"""
    health_data = {
        "status": "healthy",
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENVIRONMENT
        },
        "timestamp": time.time(),
        "services": {}
    }
    
    try:
        # Database health
        db_health = check_database_health()
        db_stats = get_database_stats()
        health_data["services"]["database"] = {
            "status": db_health.get("status", "unknown"),
            "version": db_health.get("version", "unknown"),
            "tables": {
                "messages": db_stats.get("messages_count", 0),
                "projects": db_stats.get("projects_count", 0),
                "tickets": db_stats.get("tickets_count", 0),
                "files": db_stats.get("files_count", 0),
                "users": db_stats.get("users_count", 0)
            }
        }
        
        # AI service health
        health_data["services"]["ai"] = {
            "enabled": settings.AI_ENABLED,
            "ollama_available": False,  # Would be checked in real implementation
            "custom_model_available": settings.CUSTOM_MODEL_ENABLED
        }
        
        # Feature status
        health_data["features"] = {
            "project_management": settings.FEATURE_PROJECT_MANAGEMENT,
            "ticket_system": settings.FEATURE_TICKET_SYSTEM,
            "file_upload": settings.FEATURE_FILE_UPLOAD,
            "user_authentication": settings.FEATURE_USER_AUTHENTICATION,
            "real_time_chat": settings.WEBSOCKET_ENABLED,
            "rag_system": settings.RAG_ENABLED
        }
        
        # System information
        health_data["system"] = {
            "python_version": os.sys.version,
            "platform": os.sys.platform,
            "log_level": settings.LOG_LEVEL,
            "debug_mode": settings.APP_DEBUG
        }
        
    except Exception as e:
        health_data["status"] = "degraded"
        health_data["error"] = str(e)
        enhanced_logger.error("Health check failed", error=str(e))
    
    return health_data

@app.get("/", tags=["info"])
async def comprehensive_root():
    """Comprehensive root endpoint with system information"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Enhanced Real-time Chat System with AI and Project Management",
        "environment": settings.APP_ENVIRONMENT,
        "timestamp": time.time(),
        "documentation": {
            "swagger": "/docs" if settings.APP_DEBUG else None,
            "redoc": "/redoc" if settings.APP_DEBUG else None,
            "openapi": "/openapi.json" if settings.APP_DEBUG else None
        },
        "features": [
            "Real-time chat with WebSocket support",
            "AI-powered responses and analysis",
            "Project management system",
            "Ticket and issue tracking",
            "File upload and management",
            "User authentication and management",
            "Advanced search and analytics",
            "RESTful API with comprehensive documentation"
        ],
        "endpoints": {
            "chat_ui": "/",
            "health_check": "/health",
            "api_messages": "/api/messages",
            "api_projects": "/api/projects",
            "api_tickets": "/api/tickets",
            "api_files": "/api/files",
            "websocket": "/ws"
        },
        "support": {
            "documentation": "/docs",
            "health": "/health",
            "contact": "support@chatsystem.com"
        }
    }

@app.get("/status", tags=["monitoring"])
async def system_status():
    """Detailed system status and metrics"""
    status_data = {
        "status": "operational",
        "timestamp": time.time(),
        "metrics": {},
        "configuration": {}
    }
    
    try:
        db_stats = get_database_stats()
        
        status_data["metrics"] = {
            "database": db_stats,
            "uptime": time.time() - getattr(app.state, "start_time", time.time()),
            "memory_usage": "N/A",
            "cpu_usage": "N/A"
        }

        status_data["configuration"] = {
            "ai": {
                "enabled": settings.AI_ENABLED,
                "rag_enabled": settings.RAG_ENABLED,
                "auto_respond": settings.AI_AUTO_RESPOND
            },
            "security": {
                "rate_limiting": settings.RATE_LIMIT_ENABLED,
                "cors_enabled": len(settings.CORS_ORIGINS) > 0
            },
            "features": settings.feature_config,
            "limits": {
                "max_file_size": settings.MAX_FILE_SIZE,
                "max_message_length": settings.AI_MAX_RESPONSE_LENGTH
            }
        }
        
    except Exception as e:
        status_data["status"] = "degraded"
        status_data["error"] = str(e)
    
    return status_data


# Development and debugging endpoints
if settings.APP_DEBUG:
    @app.get("/debug/config", tags=["debug"])
    async def debug_configuration():
        """Debug endpoint to show current configuration (development only)"""
        return {
            "app_config": settings.get_safe_settings(),
            "ai_config": settings.ai_config,
            "security_config": settings.security_config,
            "feature_config": settings.feature_config,
            "system_config": settings.system_config
        }
    
    @app.get("/debug/routes", tags=["debug"])
    async def debug_routes():
        """Debug endpoint to show all registered routes (development only)"""
        routes = []
        for route in app.routes:
            route_info = {
                "path": getattr(route, "path", None),
                "methods": getattr(route, "methods", None),
                "name": getattr(route, "name", None)
            }
            routes.append(route_info)
        return {"routes": routes}

# Application startup complete
enhanced_logger.info(
    "FastAPI application configured",
    total_routes=len(app.routes),
    debug_mode=settings.APP_DEBUG,
    environment=settings.APP_ENVIRONMENT
)

if __name__ == "__main__":
    import uvicorn
    
    enhanced_logger.info(
        "Starting Uvicorn server",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS
    )
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS if not settings.RELOAD else 1,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        timeout_keep_alive=5,
        timeout_notify=30,
        timeout_graceful_shutdown=30
    )