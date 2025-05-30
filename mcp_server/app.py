from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp_server.config import get_settings
from mcp_server.routers import claim_status, configurations, auth

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="MCP Server for Availity Enhanced Claim Status APIs",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    auth.router,
    prefix=settings.API_PREFIX,
    tags=["auth"]
)
app.include_router(
    claim_status.router,
    prefix=settings.API_PREFIX,
    tags=["claim-status"]
)
app.include_router(
    configurations.router,
    prefix=settings.API_PREFIX,
    tags=["configurations"]
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"} 

@app.get("/routes")
def list_routes():
    return [route.path for route in app.router.routes]