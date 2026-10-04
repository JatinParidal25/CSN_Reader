from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FieldMetadata(BaseModel):
    name: str
    label: Optional[str] = None
    type: Optional[str] = None
    native_type: Optional[str] = None
    key: bool = False
    nullable: bool = True
    is_measure: bool = False
    aggregation: Optional[str] = None
    measure_type: Optional[str] = None
    semantic_type: Optional[str] = None
    foreign_key_association: Optional[str] = None
    navigation_attribute_ref: Optional[List[str]] = None
    length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    source_mapping: Optional[Dict[str, Any]] = None


class AssociationMetadata(BaseModel):
    name: str
    target: str
    cardinality: Optional[str] = None
    relationship_type: str = "ASSOCIATION"
    label: Optional[str] = None
    on_condition: Optional[Any] = None
    source_key: Optional[str] = None


class HierarchyLevel(BaseModel):
    name: Optional[str] = None
    element: Optional[str] = None


class HierarchyMetadata(BaseModel):
    name: str
    label: Optional[str] = None
    levels: List[str] = []


class ObjectMetadata(BaseModel):
    name: str
    label: Optional[str] = None
    kind: str = "entity"  # entity, context, type, analytic_model, etc.
    modeling_pattern: Optional[str] = None  # ANALYTICAL_CUBE, ANALYTICAL_FACT, ANALYTICAL_DIMENSION, etc.
    supported_capabilities: List[str] = Field(default_factory=list)
    source_objects: List[str] = Field(default_factory=list)
    fields: List[FieldMetadata] = Field(default_factory=list)
    measures: List[FieldMetadata] = Field(default_factory=list)
    associations: List[AssociationMetadata] = Field(default_factory=list)
    hierarchies: List[HierarchyMetadata] = Field(default_factory=list)
    annotations: Dict[str, Any] = Field(default_factory=dict)
    folder_assignment: Optional[str] = None
    description: Optional[str] = None


class Relationship(BaseModel):
    source: str
    target: str
    relationship_type: str  # SOURCE, ASSOCIATION, FOREIGN_KEY, PROJECTION, FACT_SOURCE, DIMENSION_SOURCE, DEPENDS_ON
    field: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ParsedCSN(BaseModel):
    filename: str
    version: Optional[str] = None
    objects: List[ObjectMetadata] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    object_count: int = 0
    relationship_count: int = 0
    field_count: int = 0
    measure_count: int = 0
