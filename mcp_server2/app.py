from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routers import selenium_router
from services.container_service import ContainerManager, SessionResponse, StatusResponse
from pydantic import BaseModel
from typing import Optional, Dict
from fastapi.responses import JSONResponse

app = FastAPI(title="Selenium MCP Server")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize container manager
container_manager = ContainerManager()

# Include routers
app.include_router(selenium_router.router, prefix="/api/v1")

class DebugResponse(BaseModel):
    session_id: str
    status: str
    active_sessions: Dict[str, str]

@app.post("/api/v1/sessions", response_model=DebugResponse)
async def create_session():
    """Create a new browser session"""
    try:
        result = await container_manager.create_session()
        # Get list of active sessions
        active_sessions = {k: "active" for k in container_manager.sessions.keys()}
        return DebugResponse(
            session_id=result.session_id,
            status=result.status,
            active_sessions=active_sessions
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/sessions/{session_id}", response_model=StatusResponse)
async def delete_session(session_id: str):
    """Delete a browser session"""
    try:
        result = await container_manager.delete_session(session_id)
        if result.status == "not_found":
            raise HTTPException(status_code=404, detail="Session not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/sessions/{session_id}", response_model=StatusResponse)
async def get_session(session_id: str):
    """Get session status"""
    try:
        result = await container_manager.get_session(session_id)
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 