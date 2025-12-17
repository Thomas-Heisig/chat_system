# routes/search.py
"""Advanced search API endpoints for messages, users, projects, and tickets"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from config.settings import enhanced_logger
from database.models import MessageType, PaginatedResponse
from database.repositories import (
    MessageRepository,
    ProjectRepository,
    TicketRepository,
    UserRepository,
)

router = APIRouter()

# Initialize repositories
message_repo = MessageRepository()
user_repo = UserRepository()
project_repo = ProjectRepository()
ticket_repo = TicketRepository()


@router.get("/api/search/messages")
async def search_messages(
    query: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(50, description="Maximum results to return", ge=1, le=500),
    offset: int = Query(0, description="Offset for pagination", ge=0),
    username: Optional[str] = Query(None, description="Filter by username"),
    message_type: Optional[MessageType] = Query(None, description="Filter by message type"),
    room_id: Optional[str] = Query(None, description="Filter by room ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    date_from: Optional[datetime] = Query(None, description="Filter messages from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter messages until this date"),
):
    """
    Advanced message search with full-text search capabilities
    
    Search across message content, usernames, and metadata with various filters.
    
    - **query**: Search term (searches in message content)
    - **limit**: Maximum number of results
    - **offset**: Pagination offset
    - **username**: Filter by specific user
    - **message_type**: Filter by message type (user, ai, system, etc.)
    - **room_id**: Filter by chat room
    - **project_id**: Filter by project
    - **date_from**: Start date for search range
    - **date_to**: End date for search range
    """
    try:
        start_time = datetime.now()

        enhanced_logger.info(
            "Message search requested",
            query=query,
            limit=limit,
            offset=offset,
            filters={
                "username": username,
                "type": message_type,
                "room_id": room_id,
                "project_id": project_id,
            },
        )

        # Get all messages that match basic filters
        messages = message_repo.get_messages(limit=10000)  # Get larger set for search

        # Apply filters
        filtered_messages = []
        search_query_lower = query.lower()

        for msg in messages:
            # Text search in content
            if search_query_lower not in msg.content.lower():
                continue

            # Apply filters
            if username and msg.username != username:
                continue
            if message_type and msg.type != message_type:
                continue
            if room_id and msg.room_id != room_id:
                continue
            if project_id and msg.project_id != project_id:
                continue
            if date_from and msg.created_at < date_from:
                continue
            if date_to and msg.created_at > date_to:
                continue

            filtered_messages.append(msg)

        # Sort by relevance (for now, by date descending)
        filtered_messages.sort(key=lambda x: x.created_at, reverse=True)

        # Apply pagination
        total = len(filtered_messages)
        paginated_messages = filtered_messages[offset : offset + limit]

        duration = (datetime.now() - start_time).total_seconds()

        enhanced_logger.info(
            "Message search completed",
            query=query,
            total_found=total,
            returned=len(paginated_messages),
            duration_seconds=duration,
        )

        return {
            "query": query,
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": [msg.model_dump() for msg in paginated_messages],
            "search_duration_seconds": duration,
            "has_more": (offset + limit) < total,
        }

    except Exception as e:
        enhanced_logger.error("Message search failed", query=query, error=str(e))
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/api/search/users")
async def search_users(
    query: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(50, description="Maximum results to return", ge=1, le=500),
):
    """
    Search for users by username, email, or display name
    
    - **query**: Search term
    - **limit**: Maximum number of results
    """
    try:
        enhanced_logger.info("User search requested", query=query, limit=limit)

        users = user_repo.get_users(limit=10000)
        search_query_lower = query.lower()

        # Search in username, email, display_name
        matching_users = []
        for user in users:
            if (
                search_query_lower in user.username.lower()
                or (user.email and search_query_lower in user.email.lower())
                or (user.display_name and search_query_lower in user.display_name.lower())
            ):
                matching_users.append(user)

        # Limit results
        matching_users = matching_users[:limit]

        enhanced_logger.info("User search completed", query=query, found=len(matching_users))

        return {
            "query": query,
            "total": len(matching_users),
            "results": [user.model_dump() for user in matching_users],
        }

    except Exception as e:
        enhanced_logger.error("User search failed", query=query, error=str(e))
        raise HTTPException(status_code=500, detail="User search failed")


@router.get("/api/search/projects")
async def search_projects(
    query: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(50, description="Maximum results to return", ge=1, le=500),
):
    """
    Search for projects by name or description
    
    - **query**: Search term
    - **limit**: Maximum number of results
    """
    try:
        enhanced_logger.info("Project search requested", query=query, limit=limit)

        projects = project_repo.get_projects(limit=10000)
        search_query_lower = query.lower()

        # Search in name and description
        matching_projects = []
        for project in projects:
            if (
                search_query_lower in project.name.lower()
                or (project.description and search_query_lower in project.description.lower())
            ):
                matching_projects.append(project)

        # Limit results
        matching_projects = matching_projects[:limit]

        enhanced_logger.info("Project search completed", query=query, found=len(matching_projects))

        return {
            "query": query,
            "total": len(matching_projects),
            "results": [project.model_dump() for project in matching_projects],
        }

    except Exception as e:
        enhanced_logger.error("Project search failed", query=query, error=str(e))
        raise HTTPException(status_code=500, detail="Project search failed")


@router.get("/api/search/tickets")
async def search_tickets(
    query: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(50, description="Maximum results to return", ge=1, le=500),
    project_id: Optional[str] = Query(None, description="Filter by project"),
):
    """
    Search for tickets by title or description
    
    - **query**: Search term
    - **limit**: Maximum number of results
    - **project_id**: Optional project filter
    """
    try:
        enhanced_logger.info(
            "Ticket search requested", query=query, limit=limit, project_id=project_id
        )

        tickets = ticket_repo.get_tickets(limit=10000, project_id=project_id)
        search_query_lower = query.lower()

        # Search in title and description
        matching_tickets = []
        for ticket in tickets:
            if (
                search_query_lower in ticket.title.lower()
                or (ticket.description and search_query_lower in ticket.description.lower())
            ):
                matching_tickets.append(ticket)

        # Limit results
        matching_tickets = matching_tickets[:limit]

        enhanced_logger.info("Ticket search completed", query=query, found=len(matching_tickets))

        return {
            "query": query,
            "total": len(matching_tickets),
            "results": [ticket.model_dump() for ticket in matching_tickets],
        }

    except Exception as e:
        enhanced_logger.error("Ticket search failed", query=query, error=str(e))
        raise HTTPException(status_code=500, detail="Ticket search failed")


@router.get("/api/search/global")
async def global_search(
    query: str = Query(..., description="Search query", min_length=1),
    limit_per_type: int = Query(10, description="Results per category", ge=1, le=100),
):
    """
    Perform a global search across all entities (messages, users, projects, tickets)
    
    Returns results from all categories in a single response.
    
    - **query**: Search term
    - **limit_per_type**: Maximum results per category
    """
    try:
        start_time = datetime.now()

        enhanced_logger.info("Global search requested", query=query, limit=limit_per_type)

        results: Dict[str, List] = {
            "messages": [],
            "users": [],
            "projects": [],
            "tickets": [],
        }

        search_query_lower = query.lower()

        # Search messages
        try:
            messages = message_repo.get_messages(limit=1000)
            for msg in messages:
                if search_query_lower in msg.content.lower():
                    results["messages"].append(msg.model_dump())
                    if len(results["messages"]) >= limit_per_type:
                        break
        except Exception as e:
            enhanced_logger.warning("Message search in global search failed", error=str(e))

        # Search users
        try:
            users = user_repo.get_users(limit=1000)
            for user in users:
                if (
                    search_query_lower in user.username.lower()
                    or (user.email and search_query_lower in user.email.lower())
                ):
                    results["users"].append(user.model_dump())
                    if len(results["users"]) >= limit_per_type:
                        break
        except Exception as e:
            enhanced_logger.warning("User search in global search failed", error=str(e))

        # Search projects
        try:
            projects = project_repo.get_projects(limit=1000)
            for project in projects:
                if search_query_lower in project.name.lower():
                    results["projects"].append(project.model_dump())
                    if len(results["projects"]) >= limit_per_type:
                        break
        except Exception as e:
            enhanced_logger.warning("Project search in global search failed", error=str(e))

        # Search tickets
        try:
            tickets = ticket_repo.get_tickets(limit=1000)
            for ticket in tickets:
                if search_query_lower in ticket.title.lower():
                    results["tickets"].append(ticket.model_dump())
                    if len(results["tickets"]) >= limit_per_type:
                        break
        except Exception as e:
            enhanced_logger.warning("Ticket search in global search failed", error=str(e))

        total_results = sum(len(v) for v in results.values())
        duration = (datetime.now() - start_time).total_seconds()

        enhanced_logger.info(
            "Global search completed",
            query=query,
            total_results=total_results,
            duration_seconds=duration,
        )

        return {
            "query": query,
            "results": results,
            "total_results": total_results,
            "results_by_type": {k: len(v) for k, v in results.items()},
            "search_duration_seconds": duration,
        }

    except Exception as e:
        enhanced_logger.error("Global search failed", query=query, error=str(e))
        raise HTTPException(status_code=500, detail="Global search failed")


@router.get("/api/search/suggestions")
async def get_search_suggestions(
    query: str = Query(..., description="Partial search query", min_length=1),
    limit: int = Query(10, description="Maximum suggestions", ge=1, le=50),
):
    """
    Get search suggestions based on partial query
    
    Returns recent and popular search terms that match the partial query.
    
    - **query**: Partial search term
    - **limit**: Maximum number of suggestions
    """
    try:
        # In production, this would use a search index or Redis cache
        # For now, return simple suggestions based on existing data

        suggestions = []
        search_query_lower = query.lower()

        # Get unique usernames that match
        users = user_repo.get_users(limit=100)
        usernames = set()
        for user in users:
            if search_query_lower in user.username.lower():
                usernames.add(user.username)
                if len(usernames) >= limit // 2:
                    break

        suggestions.extend([{"type": "user", "text": username} for username in usernames])

        # Get project names that match
        projects = project_repo.get_projects(limit=100)
        project_names = set()
        for project in projects:
            if search_query_lower in project.name.lower():
                project_names.add(project.name)
                if len(project_names) >= limit // 2:
                    break

        suggestions.extend([{"type": "project", "text": name} for name in project_names])

        # Limit total suggestions
        suggestions = suggestions[:limit]

        enhanced_logger.info("Search suggestions generated", query=query, count=len(suggestions))

        return {"query": query, "suggestions": suggestions, "total": len(suggestions)}

    except Exception as e:
        enhanced_logger.error("Failed to generate search suggestions", query=query, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate suggestions")
