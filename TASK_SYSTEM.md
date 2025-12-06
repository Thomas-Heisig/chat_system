# Task and Project Management System Guide

**Version:** 2.0.0  
**Last Updated:** 2025-12-06  
**Estimated Reading Time:** 25 minutes

## 📋 Table of Contents

- [Overview](#overview)
- [Project Management](#project-management)
- [Ticket System](#ticket-system)
- [Task Workflows](#task-workflows)
- [Team Collaboration](#team-collaboration)
- [Reporting and Analytics](#reporting-and-analytics)
- [Integration with Chat](#integration-with-chat)

## Overview

The Task System provides comprehensive project and ticket management capabilities integrated directly into the chat platform. This enables teams to manage work, track progress, and collaborate seamlessly without leaving the conversation context.

### System Architecture

```
┌─────────────┐
│   Projects  │ ← Top-level organization
└──────┬──────┘
       │
       ├─── 📊 Metadata (name, description, dates)
       ├─── 👥 Team members & roles
       ├─── 🏷️  Tags & categories
       └─── 📈 Analytics
              │
              ▼
       ┌─────────────┐
       │   Tickets   │ ← Individual work items
       └──────┬──────┘
              │
              ├─── 🎫 Type (Task, Bug, Feature, etc.)
              ├─── ⚡ Priority (Low, Medium, High, Critical)
              ├─── 📍 Status (Open, In Progress, Resolved, Closed)
              ├─── 👤 Assignee & Reporter
              ├─── 📎 Attachments
              ├─── 💬 Comments & Activity
              └─── ⏰ Due dates & time tracking
```

### Key Features

**Projects**:
- Multi-project support
- Team assignment and roles
- Project templates
- Milestones and sprints
- Custom fields

**Tickets**:
- Multiple ticket types
- Priority levels
- Status workflow
- File attachments
- Time tracking
- Custom labels

**Collaboration**:
- Real-time updates
- @mentions and notifications
- Activity feed
- Comment threads
- Integration with chat

## Project Management

### 1. Project Structure

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

class ProjectStatus(Enum):
    """Project status"""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"

@dataclass
class Project:
    """Project model"""
    id: str
    name: str
    description: str
    status: ProjectStatus
    owner_id: str
    
    # Dates
    created_at: datetime
    updated_at: datetime
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Organization
    tags: List[str] = None
    category: Optional[str] = None
    
    # Team
    team_members: List[str] = None
    
    # Metrics
    ticket_count: int = 0
    completed_tickets: int = 0
    
    # Configuration
    settings: dict = None
    custom_fields: dict = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.team_members is None:
            self.team_members = []
        if self.settings is None:
            self.settings = {}
        if self.custom_fields is None:
            self.custom_fields = {}
    
    def completion_rate(self) -> float:
        """Calculate project completion rate"""
        if self.ticket_count == 0:
            return 0.0
        return (self.completed_tickets / self.ticket_count) * 100
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "tags": self.tags,
            "category": self.category,
            "team_members": self.team_members,
            "ticket_count": self.ticket_count,
            "completed_tickets": self.completed_tickets,
            "completion_rate": self.completion_rate(),
            "settings": self.settings,
            "custom_fields": self.custom_fields
        }
```

### 2. Project Operations

```python
class ProjectService:
    """Project management service"""
    
    def __init__(self, repository):
        self.repo = repository
    
    async def create_project(
        self,
        name: str,
        description: str,
        owner_id: str,
        **kwargs
    ) -> Project:
        """Create a new project"""
        
        project = Project(
            id=generate_uuid(),
            name=name,
            description=description,
            status=ProjectStatus.PLANNING,
            owner_id=owner_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            **kwargs
        )
        
        # Save to database
        await self.repo.save_project(project)
        
        # Create activity log
        await self.log_activity(
            project_id=project.id,
            user_id=owner_id,
            action="created",
            details={"name": name}
        )
        
        logger.info(f"Created project: {project.id} - {name}")
        
        return project
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        return await self.repo.get_project(project_id)
    
    async def update_project(
        self,
        project_id: str,
        user_id: str,
        **updates
    ) -> Project:
        """Update project"""
        
        project = await self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Check permission
        if not await self.can_edit_project(user_id, project):
            raise PermissionError("User cannot edit this project")
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        project.updated_at = datetime.now()
        
        # Save
        await self.repo.update_project(project)
        
        # Log activity
        await self.log_activity(
            project_id=project_id,
            user_id=user_id,
            action="updated",
            details=updates
        )
        
        return project
    
    async def delete_project(self, project_id: str, user_id: str):
        """Delete project"""
        
        project = await self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Check permission (only owner or admin)
        if project.owner_id != user_id and not await self.is_admin(user_id):
            raise PermissionError("Only owner or admin can delete project")
        
        # Delete all tickets
        tickets = await self.repo.get_project_tickets(project_id)
        for ticket in tickets:
            await self.ticket_service.delete_ticket(ticket.id, user_id)
        
        # Delete project
        await self.repo.delete_project(project_id)
        
        logger.info(f"Deleted project: {project_id}")
    
    async def add_team_member(
        self,
        project_id: str,
        user_id: str,
        member_id: str,
        role: str = "member"
    ):
        """Add team member to project"""
        
        project = await self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Check permission
        if not await self.can_manage_team(user_id, project):
            raise PermissionError("User cannot manage project team")
        
        # Add member
        if member_id not in project.team_members:
            project.team_members.append(member_id)
            
            # Store role
            if "team_roles" not in project.settings:
                project.settings["team_roles"] = {}
            project.settings["team_roles"][member_id] = role
            
            await self.repo.update_project(project)
            
            # Log activity
            await self.log_activity(
                project_id=project_id,
                user_id=user_id,
                action="added_member",
                details={"member_id": member_id, "role": role}
            )
    
    async def list_projects(
        self,
        user_id: str,
        status: Optional[ProjectStatus] = None,
        include_archived: bool = False
    ) -> List[Project]:
        """List projects accessible to user"""
        
        # Get all projects where user is owner or member
        projects = await self.repo.get_user_projects(user_id)
        
        # Filter by status
        if status:
            projects = [p for p in projects if p.status == status]
        
        # Filter archived
        if not include_archived:
            projects = [p for p in projects if p.status != ProjectStatus.ARCHIVED]
        
        return projects
    
    async def get_project_stats(self, project_id: str) -> dict:
        """Get project statistics"""
        
        project = await self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Get tickets
        tickets = await self.repo.get_project_tickets(project_id)
        
        # Calculate stats
        total = len(tickets)
        by_status = {}
        by_priority = {}
        by_type = {}
        
        for ticket in tickets:
            # By status
            status = ticket.status.value
            by_status[status] = by_status.get(status, 0) + 1
            
            # By priority
            priority = ticket.priority.value
            by_priority[priority] = by_priority.get(priority, 0) + 1
            
            # By type
            ticket_type = ticket.type.value
            by_type[ticket_type] = by_type.get(ticket_type, 0) + 1
        
        return {
            "total_tickets": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "by_type": by_type,
            "completion_rate": project.completion_rate(),
            "team_size": len(project.team_members)
        }
```

### 3. Project Templates

```python
class ProjectTemplate:
    """Project template for quick setup"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.default_tickets = []
        self.default_settings = {}
    
    def add_default_ticket(
        self,
        title: str,
        description: str,
        type: str,
        priority: str = "medium"
    ):
        """Add default ticket to template"""
        self.default_tickets.append({
            "title": title,
            "description": description,
            "type": type,
            "priority": priority
        })
    
    async def create_from_template(
        self,
        project_service,
        name: str,
        owner_id: str
    ) -> Project:
        """Create project from template"""
        
        # Create project
        project = await project_service.create_project(
            name=name,
            description=self.description,
            owner_id=owner_id,
            settings=self.default_settings.copy()
        )
        
        # Create default tickets
        for ticket_def in self.default_tickets:
            await project_service.ticket_service.create_ticket(
                project_id=project.id,
                reporter_id=owner_id,
                **ticket_def
            )
        
        return project

# Example templates
SOFTWARE_PROJECT_TEMPLATE = ProjectTemplate(
    name="Software Development",
    description="Standard software development project"
)
SOFTWARE_PROJECT_TEMPLATE.add_default_ticket(
    "Project Setup",
    "Initialize repository and development environment",
    "task",
    "high"
)
SOFTWARE_PROJECT_TEMPLATE.add_default_ticket(
    "Architecture Design",
    "Design system architecture and document",
    "task",
    "high"
)
SOFTWARE_PROJECT_TEMPLATE.add_default_ticket(
    "Implementation",
    "Implement core features",
    "task",
    "medium"
)
SOFTWARE_PROJECT_TEMPLATE.add_default_ticket(
    "Testing",
    "Write and execute tests",
    "task",
    "high"
)
SOFTWARE_PROJECT_TEMPLATE.add_default_ticket(
    "Documentation",
    "Create user and developer documentation",
    "task",
    "medium"
)
```

## Ticket System

### 1. Ticket Structure

```python
class TicketType(Enum):
    """Ticket types"""
    TASK = "task"
    BUG = "bug"
    FEATURE = "feature"
    ENHANCEMENT = "enhancement"
    QUESTION = "question"
    INCIDENT = "incident"

class TicketPriority(Enum):
    """Ticket priorities"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TicketStatus(Enum):
    """Ticket statuses"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    CLOSED = "closed"
    BLOCKED = "blocked"

@dataclass
class Ticket:
    """Ticket model"""
    id: str
    project_id: str
    title: str
    description: str
    
    # Classification
    type: TicketType
    priority: TicketPriority
    status: TicketStatus
    
    # People
    reporter_id: str
    assignee_id: Optional[str] = None
    
    # Dates
    created_at: datetime = None
    updated_at: datetime = None
    due_date: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Organization
    tags: List[str] = None
    labels: List[str] = None
    
    # Tracking
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    
    # Relations
    parent_id: Optional[str] = None
    blocked_by: List[str] = None
    
    # Attachments
    attachments: List[str] = None
    
    # Metadata
    custom_fields: dict = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.tags is None:
            self.tags = []
        if self.labels is None:
            self.labels = []
        if self.blocked_by is None:
            self.blocked_by = []
        if self.attachments is None:
            self.attachments = []
        if self.custom_fields is None:
            self.custom_fields = {}
    
    def is_overdue(self) -> bool:
        """Check if ticket is overdue"""
        if not self.due_date:
            return False
        if self.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            return False
        return datetime.now() > self.due_date
    
    def time_to_resolution(self) -> Optional[timedelta]:
        """Calculate time to resolution"""
        if not self.resolved_at:
            return None
        return self.resolved_at - self.created_at
```

### 2. Ticket Operations

```python
class TicketService:
    """Ticket management service"""
    
    def __init__(self, repository):
        self.repo = repository
    
    async def create_ticket(
        self,
        project_id: str,
        title: str,
        description: str,
        type: TicketType,
        priority: TicketPriority,
        reporter_id: str,
        **kwargs
    ) -> Ticket:
        """Create a new ticket"""
        
        ticket = Ticket(
            id=generate_uuid(),
            project_id=project_id,
            title=title,
            description=description,
            type=type,
            priority=priority,
            status=TicketStatus.OPEN,
            reporter_id=reporter_id,
            **kwargs
        )
        
        # Save to database
        await self.repo.save_ticket(ticket)
        
        # Update project stats
        await self.update_project_ticket_count(project_id, 1)
        
        # Create activity log
        await self.log_activity(
            ticket_id=ticket.id,
            user_id=reporter_id,
            action="created",
            details={"title": title, "type": type.value}
        )
        
        # Notify assignee if set
        if ticket.assignee_id:
            await self.notify_user(
                ticket.assignee_id,
                f"New ticket assigned: {title}",
                ticket_id=ticket.id
            )
        
        return ticket
    
    async def update_ticket(
        self,
        ticket_id: str,
        user_id: str,
        **updates
    ) -> Ticket:
        """Update ticket"""
        
        ticket = await self.repo.get_ticket(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        # Track changes for activity log
        changes = {}
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(ticket, key):
                old_value = getattr(ticket, key)
                if old_value != value:
                    changes[key] = {"old": old_value, "new": value}
                    setattr(ticket, key, value)
        
        ticket.updated_at = datetime.now()
        
        # Special handling for status changes
        if "status" in changes:
            if value == TicketStatus.RESOLVED:
                ticket.resolved_at = datetime.now()
                await self.update_project_completed_count(ticket.project_id, 1)
        
        # Save
        await self.repo.update_ticket(ticket)
        
        # Log activity
        if changes:
            await self.log_activity(
                ticket_id=ticket_id,
                user_id=user_id,
                action="updated",
                details=changes
            )
        
        # Notify stakeholders
        await self.notify_ticket_update(ticket, changes, user_id)
        
        return ticket
    
    async def assign_ticket(
        self,
        ticket_id: str,
        assignee_id: str,
        assigned_by: str
    ):
        """Assign ticket to user"""
        
        await self.update_ticket(
            ticket_id,
            assigned_by,
            assignee_id=assignee_id
        )
        
        # Notify assignee
        ticket = await self.repo.get_ticket(ticket_id)
        await self.notify_user(
            assignee_id,
            f"Ticket assigned to you: {ticket.title}",
            ticket_id=ticket_id
        )
    
    async def add_comment(
        self,
        ticket_id: str,
        user_id: str,
        content: str
    ):
        """Add comment to ticket"""
        
        comment = {
            "id": generate_uuid(),
            "ticket_id": ticket_id,
            "user_id": user_id,
            "content": content,
            "created_at": datetime.now().isoformat()
        }
        
        await self.repo.save_comment(comment)
        
        # Log activity
        await self.log_activity(
            ticket_id=ticket_id,
            user_id=user_id,
            action="commented",
            details={"content": content[:100]}
        )
        
        # Notify watchers
        await self.notify_ticket_comment(ticket_id, user_id, content)
        
        return comment
    
    async def attach_file(
        self,
        ticket_id: str,
        file_id: str,
        user_id: str
    ):
        """Attach file to ticket"""
        
        ticket = await self.repo.get_ticket(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        ticket.attachments.append(file_id)
        await self.repo.update_ticket(ticket)
        
        # Log activity
        await self.log_activity(
            ticket_id=ticket_id,
            user_id=user_id,
            action="attached_file",
            details={"file_id": file_id}
        )
    
    async def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get ticket by ID"""
        return await self.repo.get_ticket(ticket_id)
    
    async def list_tickets(
        self,
        project_id: Optional[str] = None,
        status: Optional[TicketStatus] = None,
        assignee_id: Optional[str] = None,
        priority: Optional[TicketPriority] = None,
        type: Optional[TicketType] = None,
        tags: Optional[List[str]] = None
    ) -> List[Ticket]:
        """List tickets with filters"""
        
        filters = {}
        if project_id:
            filters["project_id"] = project_id
        if status:
            filters["status"] = status
        if assignee_id:
            filters["assignee_id"] = assignee_id
        if priority:
            filters["priority"] = priority
        if type:
            filters["type"] = type
        if tags:
            filters["tags"] = tags
        
        return await self.repo.list_tickets(**filters)
```

### 3. Ticket Workflows

```python
class TicketWorkflow:
    """Manage ticket status workflows"""
    
    # Define allowed status transitions
    TRANSITIONS = {
        TicketStatus.OPEN: [
            TicketStatus.IN_PROGRESS,
            TicketStatus.CLOSED
        ],
        TicketStatus.IN_PROGRESS: [
            TicketStatus.IN_REVIEW,
            TicketStatus.BLOCKED,
            TicketStatus.OPEN
        ],
        TicketStatus.IN_REVIEW: [
            TicketStatus.RESOLVED,
            TicketStatus.IN_PROGRESS
        ],
        TicketStatus.BLOCKED: [
            TicketStatus.IN_PROGRESS,
            TicketStatus.OPEN
        ],
        TicketStatus.RESOLVED: [
            TicketStatus.CLOSED,
            TicketStatus.IN_PROGRESS  # Reopen
        ],
        TicketStatus.CLOSED: [
            TicketStatus.IN_PROGRESS  # Reopen
        ]
    }
    
    def can_transition(
        self,
        from_status: TicketStatus,
        to_status: TicketStatus
    ) -> bool:
        """Check if status transition is allowed"""
        return to_status in self.TRANSITIONS.get(from_status, [])
    
    async def transition(
        self,
        ticket_service,
        ticket_id: str,
        new_status: TicketStatus,
        user_id: str,
        reason: str = None
    ):
        """Transition ticket to new status"""
        
        ticket = await ticket_service.get_ticket(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        # Check if transition is allowed
        if not self.can_transition(ticket.status, new_status):
            raise ValueError(
                f"Cannot transition from {ticket.status.value} to {new_status.value}"
            )
        
        # Perform transition
        await ticket_service.update_ticket(
            ticket_id,
            user_id,
            status=new_status
        )
        
        # Log reason if provided
        if reason:
            await ticket_service.add_comment(
                ticket_id,
                user_id,
                f"Status changed to {new_status.value}: {reason}"
            )
```

## Task Workflows

### 1. Automation Rules

```python
class AutomationRule:
    """Automation rule for tickets"""
    
    def __init__(self, name: str, condition, action):
        self.name = name
        self.condition = condition  # Function that returns True/False
        self.action = action  # Function to execute
    
    async def should_execute(self, ticket: Ticket, event: dict) -> bool:
        """Check if rule should execute"""
        return await self.condition(ticket, event)
    
    async def execute(self, ticket: Ticket, event: dict):
        """Execute rule action"""
        await self.action(ticket, event)

# Example rules
async def high_priority_bug_condition(ticket, event):
    """Condition: High priority bug created"""
    return (
        event["type"] == "created" and
        ticket.type == TicketType.BUG and
        ticket.priority == TicketPriority.HIGH
    )

async def notify_team_action(ticket, event):
    """Action: Notify team"""
    await send_notification(
        channel="bugs",
        message=f"🚨 High priority bug: {ticket.title}",
        ticket_id=ticket.id
    )

high_priority_bug_rule = AutomationRule(
    name="notify_high_priority_bugs",
    condition=high_priority_bug_condition,
    action=notify_team_action
)

# Auto-assign rule
async def unassigned_condition(ticket, event):
    return event["type"] == "created" and not ticket.assignee_id

async def auto_assign_action(ticket, event):
    # Find team member with least assigned tickets
    assignee = await find_least_busy_member(ticket.project_id)
    if assignee:
        await ticket_service.assign_ticket(ticket.id, assignee, "system")

auto_assign_rule = AutomationRule(
    name="auto_assign_tickets",
    condition=unassigned_condition,
    action=auto_assign_action
)
```

### 2. Scheduled Tasks

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Send daily digest
@scheduler.scheduled_job('cron', hour=9, minute=0)
async def send_daily_digest():
    """Send daily ticket digest to team"""
    
    # Get all open tickets
    tickets = await ticket_service.list_tickets(status=TicketStatus.OPEN)
    
    # Group by project
    by_project = {}
    for ticket in tickets:
        if ticket.project_id not in by_project:
            by_project[ticket.project_id] = []
        by_project[ticket.project_id].append(ticket)
    
    # Send digest for each project
    for project_id, project_tickets in by_project.items():
        project = await project_service.get_project(project_id)
        
        digest = f"Daily Digest - {project.name}\n\n"
        digest += f"Open Tickets: {len(project_tickets)}\n"
        
        # High priority tickets
        high_priority = [t for t in project_tickets 
                        if t.priority == TicketPriority.HIGH]
        if high_priority:
            digest += f"\n🔴 High Priority ({len(high_priority)}):\n"
            for ticket in high_priority[:5]:
                digest += f"  - {ticket.title}\n"
        
        # Overdue tickets
        overdue = [t for t in project_tickets if t.is_overdue()]
        if overdue:
            digest += f"\n⏰ Overdue ({len(overdue)}):\n"
            for ticket in overdue[:5]:
                digest += f"  - {ticket.title}\n"
        
        await send_project_notification(project_id, digest)

# Check for stale tickets
@scheduler.scheduled_job('cron', hour=10, minute=0)
async def check_stale_tickets():
    """Alert for tickets with no activity"""
    
    cutoff = datetime.now() - timedelta(days=7)
    
    tickets = await ticket_service.list_tickets(
        status=TicketStatus.IN_PROGRESS
    )
    
    for ticket in tickets:
        if ticket.updated_at < cutoff:
            # Notify assignee
            if ticket.assignee_id:
                await notify_user(
                    ticket.assignee_id,
                    f"Ticket has been inactive for 7 days: {ticket.title}",
                    ticket_id=ticket.id
                )

scheduler.start()
```

## Team Collaboration

### 1. Notifications

```python
class NotificationService:
    """Handle ticket notifications"""
    
    async def notify_ticket_created(self, ticket: Ticket):
        """Notify on ticket creation"""
        
        # Notify project team
        project = await project_service.get_project(ticket.project_id)
        for member_id in project.team_members:
            await self.send_notification(
                user_id=member_id,
                type="ticket_created",
                title=f"New ticket: {ticket.title}",
                data={"ticket_id": ticket.id}
            )
    
    async def notify_ticket_assigned(self, ticket: Ticket, assignee_id: str):
        """Notify on ticket assignment"""
        
        await self.send_notification(
            user_id=assignee_id,
            type="ticket_assigned",
            title=f"Ticket assigned: {ticket.title}",
            data={"ticket_id": ticket.id},
            priority="high"
        )
    
    async def notify_ticket_comment(
        self,
        ticket: Ticket,
        commenter_id: str,
        comment: str
    ):
        """Notify on new comment"""
        
        # Notify assignee and reporter
        recipients = {ticket.assignee_id, ticket.reporter_id}
        recipients.discard(commenter_id)  # Don't notify commenter
        recipients.discard(None)
        
        for user_id in recipients:
            await self.send_notification(
                user_id=user_id,
                type="ticket_comment",
                title=f"New comment on: {ticket.title}",
                data={
                    "ticket_id": ticket.id,
                    "comment": comment[:100]
                }
            )
    
    async def notify_mention(
        self,
        mentioned_user_id: str,
        ticket: Ticket,
        content: str
    ):
        """Notify on @mention"""
        
        await self.send_notification(
            user_id=mentioned_user_id,
            type="mention",
            title=f"You were mentioned in: {ticket.title}",
            data={
                "ticket_id": ticket.id,
                "context": content[:200]
            },
            priority="high"
        )
```

### 2. Activity Feed

```python
class ActivityFeed:
    """Track and display ticket activity"""
    
    async def get_ticket_activity(
        self,
        ticket_id: str,
        limit: int = 50
    ) -> List[dict]:
        """Get activity for ticket"""
        
        activities = await self.repo.get_activities(
            ticket_id=ticket_id,
            limit=limit
        )
        
        return [self.format_activity(a) for a in activities]
    
    async def get_project_activity(
        self,
        project_id: str,
        limit: int = 100
    ) -> List[dict]:
        """Get activity for project"""
        
        activities = await self.repo.get_activities(
            project_id=project_id,
            limit=limit
        )
        
        return [self.format_activity(a) for a in activities]
    
    def format_activity(self, activity: dict) -> dict:
        """Format activity for display"""
        
        action = activity["action"]
        user = activity["user"]
        timestamp = activity["timestamp"]
        details = activity["details"]
        
        # Generate human-readable message
        message = self.generate_message(action, user, details)
        
        return {
            "id": activity["id"],
            "message": message,
            "action": action,
            "user": user,
            "timestamp": timestamp,
            "details": details
        }
    
    def generate_message(self, action: str, user: dict, details: dict) -> str:
        """Generate activity message"""
        
        username = user["username"]
        
        if action == "created":
            return f"{username} created the ticket"
        
        elif action == "updated":
            changes = []
            for key, change in details.items():
                changes.append(f"{key} from '{change['old']}' to '{change['new']}'")
            return f"{username} updated {', '.join(changes)}"
        
        elif action == "commented":
            return f"{username} added a comment"
        
        elif action == "assigned":
            assignee = details.get("assignee_name")
            return f"{username} assigned to {assignee}"
        
        elif action == "attached_file":
            return f"{username} attached a file"
        
        else:
            return f"{username} performed {action}"
```

## Reporting and Analytics

### 1. Project Reports

```python
class ReportGenerator:
    """Generate project and ticket reports"""
    
    async def generate_project_report(
        self,
        project_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """Generate comprehensive project report"""
        
        project = await project_service.get_project(project_id)
        tickets = await ticket_service.list_tickets(project_id=project_id)
        
        # Filter by date range
        tickets_in_range = [
            t for t in tickets
            if start_date <= t.created_at <= end_date
        ]
        
        report = {
            "project": project.to_dict(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": self.generate_summary(tickets_in_range),
            "breakdown": self.generate_breakdown(tickets_in_range),
            "team_performance": await self.generate_team_performance(
                project_id,
                tickets_in_range
            ),
            "trends": await self.generate_trends(project_id, start_date, end_date)
        }
        
        return report
    
    def generate_summary(self, tickets: List[Ticket]) -> dict:
        """Generate summary statistics"""
        
        total = len(tickets)
        if total == 0:
            return {"total": 0}
        
        completed = len([t for t in tickets 
                        if t.status == TicketStatus.RESOLVED])
        
        avg_resolution_time = None
        resolution_times = [
            t.time_to_resolution()
            for t in tickets
            if t.time_to_resolution()
        ]
        if resolution_times:
            avg_resolution_time = sum(
                [t.total_seconds() for t in resolution_times]
            ) / len(resolution_times) / 3600  # hours
        
        return {
            "total": total,
            "completed": completed,
            "completion_rate": (completed / total) * 100,
            "in_progress": len([t for t in tickets 
                               if t.status == TicketStatus.IN_PROGRESS]),
            "blocked": len([t for t in tickets 
                           if t.status == TicketStatus.BLOCKED]),
            "average_resolution_hours": avg_resolution_time
        }
    
    def generate_breakdown(self, tickets: List[Ticket]) -> dict:
        """Generate breakdown by various dimensions"""
        
        breakdown = {
            "by_type": {},
            "by_priority": {},
            "by_status": {},
            "by_assignee": {}
        }
        
        for ticket in tickets:
            # By type
            type_val = ticket.type.value
            breakdown["by_type"][type_val] = \
                breakdown["by_type"].get(type_val, 0) + 1
            
            # By priority
            priority_val = ticket.priority.value
            breakdown["by_priority"][priority_val] = \
                breakdown["by_priority"].get(priority_val, 0) + 1
            
            # By status
            status_val = ticket.status.value
            breakdown["by_status"][status_val] = \
                breakdown["by_status"].get(status_val, 0) + 1
            
            # By assignee
            if ticket.assignee_id:
                breakdown["by_assignee"][ticket.assignee_id] = \
                    breakdown["by_assignee"].get(ticket.assignee_id, 0) + 1
        
        return breakdown
```

### 2. Burndown Charts

```python
async def generate_burndown_chart(
    project_id: str,
    sprint_start: datetime,
    sprint_end: datetime
) -> dict:
    """Generate burndown chart data"""
    
    # Get all tickets in sprint
    tickets = await ticket_service.list_tickets(project_id=project_id)
    sprint_tickets = [
        t for t in tickets
        if sprint_start <= t.created_at <= sprint_end
    ]
    
    total_points = sum(t.estimated_hours or 0 for t in sprint_tickets)
    
    # Calculate remaining work per day
    current = sprint_start
    data_points = []
    
    while current <= sprint_end:
        # Count resolved tickets up to this point
        resolved = [
            t for t in sprint_tickets
            if t.resolved_at and t.resolved_at <= current
        ]
        
        completed_points = sum(t.estimated_hours or 0 for t in resolved)
        remaining_points = total_points - completed_points
        
        data_points.append({
            "date": current.isoformat(),
            "remaining": remaining_points,
            "completed": completed_points
        })
        
        current += timedelta(days=1)
    
    return {
        "total_points": total_points,
        "data_points": data_points
    }
```

## Integration with Chat

### 1. Chat Commands

```python
class TicketChatCommands:
    """Ticket commands in chat"""
    
    async def handle_command(self, message: str, user_id: str, channel: str):
        """Handle ticket-related commands"""
        
        if message.startswith("/ticket create"):
            return await self.create_ticket_from_chat(message, user_id)
        
        elif message.startswith("/ticket assign"):
            return await self.assign_ticket_from_chat(message, user_id)
        
        elif message.startswith("/ticket status"):
            return await self.update_status_from_chat(message, user_id)
        
        elif message.startswith("/ticket list"):
            return await self.list_tickets_in_chat(message, user_id)
    
    async def create_ticket_from_chat(self, message: str, user_id: str):
        """Create ticket from chat message"""
        # Parse: /ticket create [project] [title] | [description]
        
        parts = message.split("|")
        if len(parts) != 2:
            return "Usage: /ticket create [project] [title] | [description]"
        
        header = parts[0].split()
        if len(header) < 4:
            return "Usage: /ticket create [project] [title] | [description]"
        
        project_name = header[2]
        title = " ".join(header[3:])
        description = parts[1].strip()
        
        # Find project
        project = await project_service.find_by_name(project_name)
        if not project:
            return f"Project '{project_name}' not found"
        
        # Create ticket
        ticket = await ticket_service.create_ticket(
            project_id=project.id,
            title=title,
            description=description,
            type=TicketType.TASK,
            priority=TicketPriority.MEDIUM,
            reporter_id=user_id
        )
        
        return f"✅ Created ticket #{ticket.id}: {title}"
```

### 2. Inline Ticket References

```python
def parse_ticket_references(message: str) -> List[str]:
    """Extract ticket references from message"""
    import re
    
    # Match patterns like #123, TICKET-456
    pattern = r'#(\d+)|([A-Z]+-\d+)'
    matches = re.findall(pattern, message)
    
    ticket_ids = []
    for match in matches:
        if match[0]:
            ticket_ids.append(match[0])
        elif match[1]:
            ticket_ids.append(match[1])
    
    return ticket_ids

async def enrich_message_with_tickets(message: str) -> dict:
    """Enrich message with ticket information"""
    
    ticket_ids = parse_ticket_references(message)
    
    ticket_info = []
    for ticket_id in ticket_ids:
        ticket = await ticket_service.get_ticket(ticket_id)
        if ticket:
            ticket_info.append({
                "id": ticket.id,
                "title": ticket.title,
                "status": ticket.status.value,
                "priority": ticket.priority.value
            })
    
    return {
        "message": message,
        "ticket_references": ticket_info
    }
```

## Next Steps

- **[ADVANCED_FEATURES.md](ADVANCED_FEATURES.md)** - Explore advanced system capabilities
- **[Examples](examples/)** - Practical code examples
- **[API Reference](docs/04-api-reference/README.md)** - Complete API documentation

---

**Need Help?** Check the [documentation](docs/) or [open an issue](https://github.com/Thomas-Heisig/chat_system/issues).
