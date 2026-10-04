from urllib.parse import unquote
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from app.models.api_models import FieldLineageResponse, ImpactResponse, LineageResponse
from app.models.metadata_models import ObjectMetadata, ParsedCSN
from app.services.session_store import session_store

router = APIRouter(prefix="/api", tags=["metadata"])


def get_active_session(session_id: str):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found or expired. Please upload a CSN file first.",
        )
    return session


@router.get("/metadata/{session_id}", response_model=ParsedCSN)
def get_metadata(session_id: str):
    """Return complete normalized metadata for the session."""
    session = get_active_session(session_id)
    return session.parsed_csn


@router.get("/objects/{session_id}", response_model=List[ObjectMetadata])
def get_all_objects(session_id: str):
    """Return all parsed objects for the session."""
    session = get_active_session(session_id)
    return session.parsed_csn.objects


@router.get("/object/{session_id}/{object_name:path}", response_model=ObjectMetadata)
def get_object_details(session_id: str, object_name: str):
    """Return metadata for a single object. Handles URL encoded names."""
    session = get_active_session(session_id)
    decoded_name = unquote(object_name)
    obj = session.metadata_graph.get_object(decoded_name)
    if not obj:
        raise HTTPException(
            status_code=404,
            detail=f"Object '{decoded_name}' was not found in parsed CSN session.",
        )
    return obj


@router.get("/lineage/{session_id}/{object_name:path}", response_model=LineageResponse)
def get_object_lineage(session_id: str, object_name: str):
    """Return deterministic lineage for an object."""
    session = get_active_session(session_id)
    decoded_name = unquote(object_name)
    if not session.metadata_graph.graph.has_node(decoded_name):
        raise HTTPException(
            status_code=404,
            detail=f"Object '{decoded_name}' not found in lineage graph.",
        )
    return session.lineage_engine.get_object_lineage(decoded_name)


@router.get("/impact/{session_id}/{object_name:path}", response_model=ImpactResponse)
def get_object_impact(session_id: str, object_name: str):
    """Return deterministic impact analysis for an object."""
    session = get_active_session(session_id)
    decoded_name = unquote(object_name)
    if not session.metadata_graph.graph.has_node(decoded_name):
        raise HTTPException(
            status_code=404,
            detail=f"Object '{decoded_name}' not found in graph.",
        )
    return session.lineage_engine.get_impact_analysis(decoded_name)


@router.get("/field-lineage/{session_id}/{object_name:path}/{field_name}", response_model=FieldLineageResponse)
def get_field_lineage_endpoint(session_id: str, object_name: str, field_name: str):
    """Return deterministic field-level lineage."""
    session = get_active_session(session_id)
    decoded_name = unquote(object_name)
    decoded_field = unquote(field_name)
    return session.lineage_engine.get_field_lineage(decoded_name, decoded_field)
