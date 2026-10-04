from typing import Any, Dict, List, Optional, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]
    user_query: str
    session_id: str
    metadata_context: Dict[str, Any]
    tool_results: Dict[str, Any]
    tools_used: List[str]
    sources: List[Dict[str, Any]]
    final_answer: Optional[str]
