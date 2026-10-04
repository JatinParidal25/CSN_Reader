from typing import Any, Dict, List, Optional
from langchain_core.tools import tool
from app.services.session_store import session_store


def resolve_object_name(session_id: str, name_query: str) -> Optional[str]:
    """Resolve an object name or label to exact object technical name."""
    session = session_store.get_session(session_id)
    if not session:
        return None

    cleaned_query = name_query.strip().lower().replace(" ", "_").replace("-", "_")

    # 1. Exact match
    for obj in session.parsed_csn.objects:
        if obj.name.lower() == cleaned_query or obj.name.lower() == name_query.strip().lower():
            return obj.name

    # 2. Label match
    for obj in session.parsed_csn.objects:
        if obj.label and obj.label.lower() == name_query.strip().lower():
            return obj.name

    # 3. Substring match
    for obj in session.parsed_csn.objects:
        if cleaned_query in obj.name.lower() or (obj.label and cleaned_query in obj.label.lower().replace(" ", "_")):
            return obj.name

    return name_query.strip()


def get_objects(session_id: str) -> Dict[str, Any]:
    """Returns available Datasphere objects with their modeling patterns and labels."""
    session = session_store.get_session(session_id)
    if not session:
        return {"error": f"Session '{session_id}' not found."}

    objects_list = [
        {
            "name": obj.name,
            "label": obj.label,
            "type": obj.modeling_pattern or obj.kind,
            "measure_count": len(obj.measures),
            "field_count": len(obj.fields),
        }
        for obj in session.parsed_csn.objects
    ]
    return {
        "count": len(objects_list),
        "objects": objects_list,
        "object_names": [obj.name for obj in session.parsed_csn.objects],
    }


def get_object_metadata(session_id: str, object_name: str) -> Dict[str, Any]:
    """Returns complete metadata for a Datasphere object."""
    session = session_store.get_session(session_id)
    if not session:
        return {"error": f"Session '{session_id}' not found."}

    resolved_name = resolve_object_name(session_id, object_name) or object_name
    obj = session.metadata_graph.get_object(resolved_name)
    if not obj:
        return {
            "error": f"Object '{object_name}' was not found in the parsed CSN metadata.",
            "available_objects": [o.name for o in session.parsed_csn.objects],
        }

    return {
        "name": obj.name,
        "label": obj.label,
        "type": obj.modeling_pattern or obj.kind,
        "supported_capabilities": obj.supported_capabilities,
        "source_objects": obj.source_objects,
        "fields": [
            {
                "name": f.name,
                "label": f.label,
                "type": f.type,
                "key": f.key,
                "is_measure": f.is_measure,
                "aggregation": f.aggregation,
                "foreign_key_association": f.foreign_key_association,
            }
            for f in obj.fields
        ],
        "measures": [
            {
                "name": m.name,
                "label": m.label,
                "aggregation": m.aggregation,
                "measure_type": m.measure_type,
            }
            for m in obj.measures
        ],
        "associations": [
            {
                "name": a.name,
                "target": a.target,
                "cardinality": a.cardinality,
                "relationship_type": a.relationship_type,
                "label": a.label,
            }
            for a in obj.associations
        ],
        "hierarchies": [
            {
                "name": h.name,
                "label": h.label,
                "levels": h.levels,
            }
            for h in obj.hierarchies
        ],
    }


def get_lineage(session_id: str, object_name: str) -> Dict[str, Any]:
    """Returns deterministic upstream and downstream relationships for an object."""
    session = session_store.get_session(session_id)
    if not session:
        return {"error": f"Session '{session_id}' not found."}

    resolved_name = resolve_object_name(session_id, object_name) or object_name
    lin = session.lineage_engine.get_object_lineage(resolved_name)

    if not lin.nodes:
        return {
            "object": object_name,
            "error": f"Object '{object_name}' does not exist in the parsed lineage graph.",
        }

    return {
        "object": resolved_name,
        "upstream": lin.upstream,
        "downstream": lin.downstream,
        "direct_sources": session.metadata_graph.get_direct_upstream(resolved_name),
        "direct_dependents": session.metadata_graph.get_direct_downstream(resolved_name),
    }


def get_field_metadata(session_id: str, object_name: Optional[str], field_name: str) -> Dict[str, Any]:
    """Returns information about a specific field on an object (or across objects if object_name is not provided)."""
    session = session_store.get_session(session_id)
    if not session:
        return {"error": f"Session '{session_id}' not found."}

    cleaned_field = field_name.strip()

    # If object_name is provided, search specifically in that object
    if object_name:
        resolved_name = resolve_object_name(session_id, object_name) or object_name
        obj = session.metadata_graph.get_object(resolved_name)
        if obj:
            for f in obj.fields:
                if f.name.lower() == cleaned_field.lower():
                    return {
                        "object": obj.name,
                        "field": f.name,
                        "label": f.label,
                        "type": f.type,
                        "native_type": f.native_type,
                        "key": f.key,
                        "is_measure": f.is_measure,
                        "aggregation": f.aggregation,
                        "measure_type": f.measure_type,
                        "foreign_key_association": f.foreign_key_association,
                        "navigation_attribute_ref": f.navigation_attribute_ref,
                    }

    # Search across all objects
    matches: List[Dict[str, Any]] = []
    for obj in session.parsed_csn.objects:
        for f in obj.fields:
            if f.name.lower() == cleaned_field.lower():
                matches.append(
                    {
                        "object": obj.name,
                        "object_label": obj.label,
                        "field": f.name,
                        "label": f.label,
                        "type": f.type,
                        "native_type": f.native_type,
                        "key": f.key,
                        "is_measure": f.is_measure,
                        "aggregation": f.aggregation,
                        "measure_type": f.measure_type,
                        "foreign_key_association": f.foreign_key_association,
                        "navigation_attribute_ref": f.navigation_attribute_ref,
                    }
                )

    if not matches:
        return {
            "field": field_name,
            "error": f"Field '{field_name}' was not found in the parsed CSN metadata.",
        }

    return {
        "field": cleaned_field,
        "occurrences_count": len(matches),
        "occurrences": matches,
    }


def get_field_lineage(session_id: str, object_name: str, field_name: str) -> Dict[str, Any]:
    """Return deterministic field-level lineage where CSN provides enough information."""
    session = session_store.get_session(session_id)
    if not session:
        return {"error": f"Session '{session_id}' not found."}

    resolved_name = resolve_object_name(session_id, object_name) or object_name
    res = session.lineage_engine.get_field_lineage(resolved_name, field_name)
    return res.model_dump()


def get_impact_analysis(session_id: str, object_name: str) -> Dict[str, Any]:
    """Returns deterministic impact analysis for changes to an object."""
    session = session_store.get_session(session_id)
    if not session:
        return {"error": f"Session '{session_id}' not found."}

    resolved_name = resolve_object_name(session_id, object_name) or object_name
    res = session.lineage_engine.get_impact_analysis(resolved_name)
    return res.model_dump()
