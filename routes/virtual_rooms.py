# routes/virtual_rooms.py
"""
🎭 Virtual Rooms Routes
API endpoints for virtual room management.

Provides 3D/VR room functionality with spatial audio.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional

from config.settings import settings, logger
from services.virtual_room_service import get_virtual_room_service
from core.auth import get_current_active_user, User

router = APIRouter(prefix="/api/virtual-rooms", tags=["virtual_rooms"])


@router.get("/status")
async def virtual_rooms_status() -> Dict[str, Any]:
    """Get virtual rooms service status"""
    vr_service = get_virtual_room_service()
    return vr_service.get_status()


@router.post("/")
async def create_virtual_room(
    name: str, 
    owner_id: str,
    template: str = "conference",
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new virtual room"""
    vr_service = get_virtual_room_service()
    return await vr_service.create_room(name, owner_id, template, config)


@router.get("/")
async def list_virtual_rooms(
    limit: int = 20, 
    offset: int = 0,
    owner_id: Optional[str] = None
) -> Dict[str, Any]:
    """List available virtual rooms"""
    vr_service = get_virtual_room_service()
    return await vr_service.list_rooms(owner_id=owner_id, limit=limit, offset=offset)


@router.get("/{room_id}")
async def get_virtual_room(room_id: str) -> Dict[str, Any]:
    """Get virtual room details"""
    vr_service = get_virtual_room_service()
    room = await vr_service.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    return room


@router.put("/{room_id}")
async def update_virtual_room(
    room_id: str, 
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """Update a virtual room"""
    vr_service = get_virtual_room_service()
    result = await vr_service.update_room(room_id, updates)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.delete("/{room_id}")
async def delete_virtual_room(room_id: str) -> Dict[str, Any]:
    """Delete a virtual room"""
    vr_service = get_virtual_room_service()
    success = await vr_service.delete_room(room_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    return {"success": True, "message": f"Room {room_id} deleted"}


@router.post("/{room_id}/join")
async def join_virtual_room(
    room_id: str, 
    user_id: str,
    position: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """Join a virtual room"""
    vr_service = get_virtual_room_service()
    result = await vr_service.join_room(room_id, user_id, position)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{room_id}/leave")
async def leave_virtual_room(room_id: str, user_id: str) -> Dict[str, Any]:
    """Leave a virtual room"""
    vr_service = get_virtual_room_service()
    result = await vr_service.leave_room(room_id, user_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.put("/{room_id}/position")
async def update_user_position(
    room_id: str, 
    user_id: str,
    position: Dict[str, float],
    rotation: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """Update user position in virtual room"""
    vr_service = get_virtual_room_service()
    result = await vr_service.update_user_position(room_id, user_id, position, rotation)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{room_id}/spatial-audio")
async def get_spatial_audio_config(
    room_id: str, 
    listener_id: str
) -> Dict[str, Any]:
    """Get spatial audio configuration"""
    vr_service = get_virtual_room_service()
    result = await vr_service.get_spatial_audio_config(room_id, listener_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/templates/list")
async def get_room_templates() -> List[Dict[str, Any]]:
    """Get available room templates"""
    vr_service = get_virtual_room_service()
    return vr_service.get_room_templates()
