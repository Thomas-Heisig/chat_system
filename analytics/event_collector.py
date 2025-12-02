"""
📊 Event Collector

Collects and processes application events for analytics.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
from config.settings import logger


class EventCollector:
    """
    Event tracking and collection system.
    
    Features:
    - Event capture and storage
    - Real-time stream processing
    - Batching and aggregation
    - Event filtering and enrichment
    """
    
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.event_types: Dict[str, int] = defaultdict(int)
        self.max_events = 10000
        self.batch_size = 100
        self.flush_interval = 60  # seconds
        
        logger.info("📊 Event Collector initialized")
    
    async def track_event(
        self,
        event_type: str,
        properties: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track an event.
        
        Args:
            event_type: Type of event (e.g., 'message_sent', 'user_login')
            properties: Event properties
            user_id: Optional user identifier
            session_id: Optional session identifier
            
        Returns:
            Event record
        """
        event = {
            "event_id": f"evt_{datetime.now().timestamp()}",
            "event_type": event_type,
            "properties": properties,
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "collected_at": datetime.now().isoformat()
            }
        }
        
        self.events.append(event)
        self.event_types[event_type] += 1
        
        # Trim if exceeds max
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
        
        logger.debug(f"📊 Event tracked: {event_type}")
        return event
    
    async def get_events(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query events with filters.
        
        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum events to return
            
        Returns:
            List of matching events
        """
        filtered = self.events
        
        if event_type:
            filtered = [e for e in filtered if e["event_type"] == event_type]
        
        if user_id:
            filtered = [e for e in filtered if e["user_id"] == user_id]
        
        if start_time:
            filtered = [
                e for e in filtered
                if datetime.fromisoformat(e["timestamp"]) >= start_time
            ]
        
        if end_time:
            filtered = [
                e for e in filtered
                if datetime.fromisoformat(e["timestamp"]) <= end_time
            ]
        
        return filtered[-limit:]
    
    async def get_aggregations(
        self,
        time_window: timedelta = timedelta(hours=24)
    ) -> Dict[str, Any]:
        """
        Get event aggregations.
        
        Args:
            time_window: Time window for aggregations
            
        Returns:
            Aggregated statistics
        """
        cutoff = datetime.now() - time_window
        recent_events = [
            e for e in self.events
            if datetime.fromisoformat(e["timestamp"]) >= cutoff
        ]
        
        # Aggregate by type
        type_counts = defaultdict(int)
        for event in recent_events:
            type_counts[event["event_type"]] += 1
        
        # Aggregate by user
        user_counts = defaultdict(int)
        for event in recent_events:
            if event["user_id"]:
                user_counts[event["user_id"]] += 1
        
        return {
            "time_window_hours": time_window.total_seconds() / 3600,
            "total_events": len(recent_events),
            "events_by_type": dict(type_counts),
            "unique_users": len(user_counts),
            "events_by_user": dict(user_counts),
            "avg_events_per_user": len(recent_events) / max(len(user_counts), 1)
        }
    
    async def export_events(
        self,
        format: str = "json",
        file_path: Optional[str] = None
    ) -> str:
        """
        Export events to file.
        
        Args:
            format: Export format ('json', 'csv')
            file_path: Optional file path
            
        Returns:
            File path or data
        """
        if format == "json":
            data = json.dumps(self.events, indent=2)
            
            if file_path:
                with open(file_path, 'w') as f:
                    f.write(data)
                return file_path
            
            return data
        
        return ""
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collector statistics"""
        return {
            "total_events": len(self.events),
            "event_types": dict(self.event_types),
            "unique_event_types": len(self.event_types),
            "max_events": self.max_events,
            "batch_size": self.batch_size
        }


# Singleton instance
_event_collector: Optional[EventCollector] = None


def get_event_collector() -> EventCollector:
    """Get or create event collector singleton"""
    global _event_collector
    if _event_collector is None:
        _event_collector = EventCollector()
    return _event_collector
