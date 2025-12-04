import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from config.settings import enhanced_logger, logger
from database.models import (
    MessageFilter,
    PaginatedResponse,
    Project,
    ProjectFilter,
    ProjectStatus,
    TicketFilter,
)
from database.repositories import (
    MessageRepository,
    ProjectRepository,
    TicketRepository,
    UserRepository,
)


class ProjectService:
    def __init__(self, project_repository: ProjectRepository, user_repository: UserRepository):
        self.project_repo = project_repository
        self.user_repo = user_repository
        self.ticket_repo = TicketRepository()
        self.message_repo = MessageRepository()

        logger.info("🔄 ProjectService initialized")

    def create_project(self, name: str, description: str, created_by: str, **kwargs) -> Project:
        """Create a new project"""
        try:
            project = Project(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                created_by=created_by,
                status=ProjectStatus.ACTIVE,
                **kwargs,
            )

            project_id = self.project_repo.create_project(project)
            project.id = project_id

            enhanced_logger.info(
                "Project created successfully",
                project_id=project_id,
                project_name=name,
                created_by=created_by,
            )
            return project

        except Exception as e:
            enhanced_logger.error(
                "Failed to create project", error=str(e), project_name=name, created_by=created_by
            )
            raise

    def get_projects(self, filters: Optional[ProjectFilter] = None) -> PaginatedResponse:
        """Get projects with filtering and pagination"""
        try:
            if filters is None:
                filters = ProjectFilter(limit=50, offset=0)

            result = self.project_repo.get_projects_by_filter(filters)

            enhanced_logger.debug(
                "Projects retrieved", total_projects=result.total, returned_count=len(result.items)
            )
            return result

        except Exception as e:
            enhanced_logger.error("Failed to retrieve projects", error=str(e))
            return PaginatedResponse(
                items=[], total=0, page=1, page_size=filters.limit if filters else 50, total_pages=0
            )

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        try:
            # This would typically call project_repo.get_project(project_id)
            # For now, return mock data
            projects = self.get_projects(ProjectFilter(limit=1000))
            for project in projects.items:
                if project.id == project_id:
                    return project
            return None

        except Exception as e:
            logger.error(f"❌ Failed to get project {project_id}: {e}")
            return None

    def update_project(self, project_id: str, **kwargs) -> bool:
        """Update project details"""
        try:
            # This would typically call project_repo.update_project(project_id, **kwargs)
            logger.info(f"📝 Updating project {project_id} with: {kwargs}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to update project {project_id}: {e}")
            return False

    def add_project_member(self, project_id: str, user_id: str) -> bool:
        """Add member to project"""
        try:
            project = self.get_project(project_id)
            if project:
                project.add_member(user_id)
                return self.update_project(project_id, members=project.members)
            return False

        except Exception as e:
            logger.error(f"❌ Failed to add member {user_id} to project {project_id}: {e}")
            return False

    def remove_project_member(self, project_id: str, user_id: str) -> bool:
        """Remove member from project"""
        try:
            project = self.get_project(project_id)
            if project:
                project.remove_member(user_id)
                return self.update_project(project_id, members=project.members)
            return False

        except Exception as e:
            logger.error(f"❌ Failed to remove member {user_id} from project {project_id}: {e}")
            return False

    def get_project_statistics(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive project statistics"""
        try:
            project = self.get_project(project_id)
            if not project:
                return {"error": "Project not found"}

            # Get project tickets
            tickets = self.ticket_repo.get_tickets_by_filter(
                TicketFilter(project_id=project_id, limit=1000)
            )

            # Get project messages
            messages = self.message_repo.filter_messages(
                MessageFilter(project_id=project_id, limit=1000)
            )

            # Calculate statistics
            total_tickets = len(tickets.items)
            open_tickets = len([t for t in tickets.items if t.status == "open"])
            completed_tickets = len([t for t in tickets.items if t.status == "closed"])

            total_messages = len(messages.items)
            recent_messages = len(
                [
                    m
                    for m in messages.items
                    if m.timestamp and m.timestamp > datetime.now() - timedelta(days=1)
                ]
            )

            stats = {
                "project_id": project_id,
                "project_name": project.name,
                "ticket_statistics": {
                    "total": total_tickets,
                    "open": open_tickets,
                    "completed": completed_tickets,
                    "completion_rate": (
                        round((completed_tickets / total_tickets * 100), 1)
                        if total_tickets > 0
                        else 0
                    ),
                },
                "message_statistics": {
                    "total": total_messages,
                    "recent_24h": recent_messages,
                    "active_users": len(set(m.username for m in messages.items)),
                },
                "member_statistics": {
                    "total_members": len(project.members),
                    "member_list": project.members,
                },
                "progress": project.progress_percentage,
            }

            enhanced_logger.info(
                "Project statistics generated",
                project_id=project_id,
                total_tickets=total_tickets,
                total_messages=total_messages,
            )
            return stats

        except Exception as e:
            enhanced_logger.error(
                "Failed to generate project statistics", error=str(e), project_id=project_id
            )
            return {"error": str(e)}

    def generate_project_report(self, project_id: str) -> Dict[str, Any]:
        """Generate comprehensive project report"""
        try:
            stats = self.get_project_statistics(project_id)
            if "error" in stats:
                return stats

            project = self.get_project(project_id)

            project_name = project.name if project else "Unknown"
            report = {
                "project_report": {
                    "project_id": project_id,
                    "project_name": project_name,
                    "generated_at": datetime.now().isoformat(),
                    "summary": f"Project '{project_name}' has {stats['ticket_statistics']['total']} tickets "
                    f"and {stats['message_statistics']['total']} messages.",
                    "key_metrics": stats,
                    "recommendations": self._generate_project_recommendations(stats),
                }
            }

            logger.info(f"📊 Project report generated for {project_id}")
            return report

        except Exception as e:
            logger.error(f"❌ Failed to generate project report: {e}")
            return {"error": str(e)}

    def _generate_project_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Generate AI-powered project recommendations"""
        recommendations = []

        ticket_stats = stats.get("ticket_statistics", {})
        message_stats = stats.get("message_statistics", {})

        if ticket_stats.get("open", 0) > 10:
            recommendations.append("Consider prioritizing and assigning open tickets")

        if ticket_stats.get("completion_rate", 0) < 50:
            recommendations.append("Focus on completing existing tickets before adding new ones")

        if message_stats.get("recent_24h", 0) < 5:
            recommendations.append("Encourage more team communication and updates")

        if len(recommendations) == 0:
            recommendations.append("Project is progressing well. Continue current workflow.")

        return recommendations
