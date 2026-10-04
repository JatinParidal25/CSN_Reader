from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.metadata_models import ObjectMetadata, ParsedCSN, Relationship


class UploadResponse(BaseModel):
    success: bool
    session_id: str
    filename: str
    object_count: int
    relationship_count: int
    field_count: int
    measure_count: int
    message: str = "CSN parsed successfully"


class LineageNode(BaseModel):
    id: str
    label: str
    kind: Optional[str] = None
    modeling_pattern: Optional[str] = None
    is_current: bool = False


class LineageEdge(BaseModel):
    source: str
    target: str
    relationship_type: str
    label: Optional[str] = None


class LineageResponse(BaseModel):
    object_name: str
    upstream: List[str] = Field(default_factory=list)
    downstream: List[str] = Field(default_factory=list)
    nodes: List[LineageNode] = Field(default_factory=list)
    edges: List[LineageEdge] = Field(default_factory=list)
    field_lineage: Optional[Dict[str, Any]] = None


class ImpactResponse(BaseModel):
    target_object: str
    direct_dependents: List[str] = Field(default_factory=list)
    downstream_dependents: List[str] = Field(default_factory=list)
    upstream_prerequisites: List[str] = Field(default_factory=list)
    affected_count: int = 0
    severity: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    details: List[str] = Field(default_factory=list)
    affected_fields: Dict[str, List[str]] = Field(default_factory=dict)


class FieldLineageResponse(BaseModel):
    object_name: str
    field_name: str
    status: str  # "resolved", "unknown", "source_origin"
    source_entity: Optional[str] = None
    source_field: Optional[str] = None
    hops: List[Dict[str, Any]] = Field(default_factory=list)
    reason: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    answer: str
    tools_used: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
