import time
import uuid
from typing import Dict, Optional
from pydantic import BaseModel, Field
from app.graph.lineage import LineageEngine
from app.graph.metadata_graph import MetadataGraph
from app.models.metadata_models import ParsedCSN


class SessionData:
    """Holds in-memory graph, lineage engine, and parsed CSN for an active session."""

    def __init__(self, session_id: str, parsed_csn: ParsedCSN):
        self.session_id = session_id
        self.filename = parsed_csn.filename
        self.created_at = time.time()
        self.parsed_csn = parsed_csn
        self.metadata_graph = MetadataGraph(parsed_csn)
        self.lineage_engine = LineageEngine(self.metadata_graph)


class SessionStore:
    """
    In-memory session manager.
    Can easily be swapped with Redis or a persistent DB in the future.
    """

    def __init__(self):
        self._sessions: Dict[str, SessionData] = {}

    def create_session(self, parsed_csn: ParsedCSN, session_id: Optional[str] = None) -> SessionData:
        sid = session_id or str(uuid.uuid4())
        session_data = SessionData(session_id=sid, parsed_csn=parsed_csn)
        self._sessions[sid] = session_data
        return session_data

    def get_session(self, session_id: str) -> Optional[SessionData]:
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_sessions(self) -> Dict[str, str]:
        return {sid: data.filename for sid, data in self._sessions.items()}


# Global session store instance
session_store = SessionStore()
