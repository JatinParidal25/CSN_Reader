from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result: Any = None


class AgentResponse(BaseModel):
    answer: str
    tools_used: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
