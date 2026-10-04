from app.api.routes_upload import router as upload_router
from app.api.routes_metadata import router as metadata_router
from app.api.routes_agent import router as agent_router

__all__ = ["upload_router", "metadata_router", "agent_router"]
