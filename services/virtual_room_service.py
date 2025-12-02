"""
🎭 Virtual Room Service - 3D/VR Room Management

Manages virtual rooms for immersive collaboration experiences.

TODO:
- [ ] Implement 3D engine integration (Three.js/Babylon.js)
- [ ] Add spatial audio calculation
- [ ] Implement real-time position synchronization
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from config.settings import logger


class RoomTemplate(str, Enum):
    """Predefined room templates"""
    CONFERENCE = "conference"
    CLASSROOM = "classroom"
    THEATER = "theater"
    GALLERY = "gallery"
    CUSTOM = "custom"


class VirtualRoomService:
    """Virtual room management service"""
    
    def __init__(self):
        self.rooms: Dict[str, Dict[str, Any]] = {}
        logger.info("🎭 Virtual Room Service initialized")
    
    async def create_room(
        self,
        name: str,
        owner_id: str,
        template: str = "conference",
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new virtual room"""
        room_id = str(uuid.uuid4())
        
        room = {
            "room_id": room_id,
            "name": name,
            "owner_id": owner_id,
            "template": template,
            "config": config or {},
            "created_at": datetime.now().isoformat(),
            "active_users": {}
        }
        
        self.rooms[room_id] = room
        logger.info(f"Virtual room created: {name} (ID: {room_id})")
        
        return room
    
    async def get_room(self, room_id: str) -> Optional[Dict[str, Any]]:
        """Get room by ID"""
        return self.rooms.get(room_id)
    
    async def list_rooms(
        self,
        owner_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List virtual rooms"""
        rooms = list(self.rooms.values())
        
        if owner_id:
            rooms = [r for r in rooms if r.get("owner_id") == owner_id]
        
        total = len(rooms)
        rooms = rooms[offset:offset + limit]
        
        return {
            "items": rooms,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def update_room(
        self,
        room_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update room configuration"""
        if room_id not in self.rooms:
            return {"error": f"Room {room_id} not found"}
        
        room = self.rooms[room_id]
        room.update(updates)
        
        logger.info(f"Room updated: {room_id}")
        return room
    
    async def delete_room(self, room_id: str) -> bool:
        """Delete a virtual room"""
        if room_id in self.rooms:
            del self.rooms[room_id]
            logger.info(f"Room deleted: {room_id}")
            return True
        return False
    
    async def join_room(
        self,
        room_id: str,
        user_id: str,
        position: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """User joins a virtual room"""
        if room_id not in self.rooms:
            return {"error": f"Room {room_id} not found"}
        
        room = self.rooms[room_id]
        room["active_users"][user_id] = {
            "user_id": user_id,
            "position": position or {"x": 0, "y": 0, "z": 0},
            "joined_at": datetime.now().isoformat()
        }
        
        logger.info(f"User {user_id} joined room {room_id}")
        return {"success": True, "room": room}
    
    async def leave_room(
        self,
        room_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """User leaves a virtual room"""
        if room_id not in self.rooms:
            return {"error": f"Room {room_id} not found"}
        
        room = self.rooms[room_id]
        if user_id in room["active_users"]:
            del room["active_users"][user_id]
            logger.info(f"User {user_id} left room {room_id}")
            return {"success": True}
        
        return {"error": "User not in room"}
    
    async def update_user_position(
        self,
        room_id: str,
        user_id: str,
        position: Dict[str, float],
        rotation: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Update user position in room"""
        if room_id not in self.rooms:
            return {"error": f"Room {room_id} not found"}
        
        room = self.rooms[room_id]
        if user_id not in room["active_users"]:
            return {"error": "User not in room"}
        
        room["active_users"][user_id]["position"] = position
        if rotation:
            room["active_users"][user_id]["rotation"] = rotation
        
        return {"success": True, "user_data": room["active_users"][user_id]}
    
    async def get_spatial_audio_config(
        self,
        room_id: str,
        listener_id: str
    ) -> Dict[str, Any]:
        """Calculate spatial audio configuration for a listener"""
        if room_id not in self.rooms:
            return {"error": f"Room {room_id} not found"}
        
        room = self.rooms[room_id]
        if listener_id not in room["active_users"]:
            return {"error": "Listener not in room"}
        
        listener_pos = room["active_users"][listener_id]["position"]
        audio_sources = []
        
        for user_id, user_data in room["active_users"].items():
            if user_id == listener_id:
                continue
            
            user_pos = user_data["position"]
            
            # Calculate distance
            import math
            dx = user_pos["x"] - listener_pos["x"]
            dy = user_pos.get("y", 0) - listener_pos.get("y", 0)
            dz = user_pos["z"] - listener_pos["z"]
            distance = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            # Simple attenuation
            volume = max(0.0, 1.0 - (distance / 20.0))
            
            audio_sources.append({
                "user_id": user_id,
                "distance": distance,
                "volume": volume,
                "position": user_pos
            })
        
        return {
            "spatial_audio_enabled": True,
            "listener_id": listener_id,
            "audio_sources": audio_sources
        }
    
    def get_room_templates(self) -> List[Dict[str, Any]]:
        """Get available room templates"""
        return [
            {"id": t.value, "name": t.value.capitalize()}
            for t in RoomTemplate
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service": "virtual_room",
            "total_rooms": len(self.rooms),
            "active_users": sum(len(r.get("active_users", {})) for r in self.rooms.values()),
            "status": "online"
        }


# Singleton
_virtual_room_service: Optional[VirtualRoomService] = None


def get_virtual_room_service() -> VirtualRoomService:
    """Get or create the VirtualRoomService singleton"""
    global _virtual_room_service
    if _virtual_room_service is None:
        _virtual_room_service = VirtualRoomService()
    return _virtual_room_service
