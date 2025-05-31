from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
from services.browser_service import BrowserService
from services.container_service import ContainerManager

VNC_URL = "http://localhost:6090/vnc.html?host=localhost&port=6090"

router = APIRouter()
browser_service = BrowserService()

class BrowserAction(BaseModel):
    type: str
    params: Dict[str, Any]

class SessionResponse(BaseModel):
    session_id: str
    vnc_url: str

@router.post("/sessions", response_model=SessionResponse)
async def create_session(container_manager: ContainerManager = Depends()):
    """Create a new browser session"""
    try:
        session_id = str(uuid.uuid4())
        await container_manager.create_session(session_id)
        browser_service.create_driver(session_id)
        
        return SessionResponse(
            session_id=session_id,
            vnc_url=VNC_URL
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/actions")
async def execute_action(
    session_id: str,
    action: BrowserAction,
    container_manager: ContainerManager = Depends()
):
    """Execute a browser action"""
    try:
        container = await container_manager.get_session(session_id)
        if not container:
            raise HTTPException(status_code=404, detail="Session not found")

        result = browser_service.execute_action(session_id, action.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    container_manager: ContainerManager = Depends()
):
    """Delete a browser session"""
    try:
        browser_service.cleanup(session_id)
        await container_manager.cleanup_session(session_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 