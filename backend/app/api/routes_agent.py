from fastapi import APIRouter, HTTPException
from app.agent.graph import run_agent
from app.models.api_models import ChatRequest, ChatResponse
from app.services.session_store import session_store

router = APIRouter(prefix="/api", tags=["agent"])


@router.post("/chat", response_model=ChatResponse)
def chat_with_agent(req: ChatRequest):
    """Ask questions to the LangGraph AI agent about Datasphere metadata, fields, and lineage."""
    if not req.session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty.")

    session = session_store.get_session(req.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{req.session_id}' not found. Please upload a CSN file first.",
        )

    try:
        response = run_agent(session_id=req.session_id, query=req.message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
