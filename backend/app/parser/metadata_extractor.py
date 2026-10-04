from typing import Any, Dict, List, Optional, Set, Tuple
from app.models.metadata_models import (
    AssociationMetadata,
    FieldMetadata,
    HierarchyMetadata,
    ObjectMetadata,
)


def safe_get(d: Any, *keys: Any, default: Any = None) -> Any:
    """Safely traverse nested dictionaries and lists."""
    curr = d
    for key in keys:
        if isinstance(curr, dict) and key in curr:
            curr = curr[key]
        elif isinstance(curr, list) and isinstance(key, int) and 0 <= key < len(curr):
            curr = curr[key]
        else:
            return default
    return curr


def unwrap_annotation_value(val: Any) -> Any:
    """
    Unwrap CSN annotation values like:
    {"#": "ANALYTICAL_CUBE"} -> "ANALYTICAL_CUBE"
    {"=": "_FKDAT"} -> "_FKDAT"
    [{"#": "DATA_STRUCTURE"}] -> ["DATA_STRUCTURE"]
    """
    if val is None:
        return None
    if isinstance(val, dict):
        if "#" in val and len(val) == 1:
            return unwrap_annotation_value(val["#"])
        if "=" in val and len(val) == 1:
            return unwrap_annotation_value(val["="])
        return {k: unwrap_annotation_value(v) for k, v in val.items()}
    if isinstance(val, list):
        return [unwrap_annotation_value(item) for item in val]
    return val


def get_first_annotation(data: Dict[str, Any], *annotation_names: str) -> Any:
    """Find the first matching annotation across possible key names."""
    if not isinstance(data, dict):
        return None
    for name in annotation_names:
        if name in data:
            return unwrap_annotation_value(data[name])
    return None


def extract_query_sources(from_node: Any, current_obj_name: str = "") -> Set[str]:
    """
    Recursively extract source entity names referenced in query.SELECT.from clauses.
    Handles:
    - {"ref": ["EntityName"]}
    - {"ref": ["EntityName", "FieldName"]} -> EntityName
    - {"SELECT": {"from": ...}}
    - {"join": "...", "args": [...]}
    - Lists of sources
    """
    sources: Set[str] = set()
    if not from_node:
        return sources

    if isinstance(from_node, dict):
        # Case: ref
        if "ref" in from_node and isinstance(from_node["ref"], list) and len(from_node["ref"]) > 0:
            ref_first = from_node["ref"][0]
            if isinstance(ref_first, str) and ref_first not in ("$projection", "$self", current_obj_name):
                # Filter out pure join aliases or aliases that might not be entities, but keep potential entity names
                sources.add(ref_first)

        # Case: SELECT subquery
        if "SELECT" in from_node and isinstance(from_node["SELECT"], dict):
            sources.update(extract_query_sources(from_node["SELECT"].get("from"), current_obj_name))

        # Case: join args
        if "args" in from_node and isinstance(from_node["args"], list):
            for arg in from_node["args"]:
                sources.update(extract_query_sources(arg, current_obj_name))

        # Nested from
        if "from" in from_node:
            sources.update(extract_query_sources(from_node["from"], current_obj_name))

    elif isinstance(from_node, list):
        for item in from_node:
            sources.update(extract_query_sources(item, current_obj_name))

    return sources


def extract_field_source_mappings(query_select: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract field projection lineage from query.SELECT.columns.
    E.g. columns with ref: ["VBRP", "NETWR"] as "NETWR"
    """
    mappings: Dict[str, Dict[str, Any]] = {}
    if not isinstance(query_select, dict):
        return mappings

    columns = query_select.get("columns", [])
    if not isinstance(columns, list):
        return mappings

    for col in columns:
        if not isinstance(col, dict):
            continue
        ref = col.get("ref")
        as_name = col.get("as")
        if isinstance(ref, list) and len(ref) > 0:
            target_name = as_name or ref[-1]
            if len(ref) >= 2:
                source_entity = ref[0]
                source_col = ref[1]
                mappings[target_name] = {
                    "source_entity": source_entity,
                    "source_field": source_col,
                }
            elif len(ref) == 1:
                mappings[target_name] = {
                    "source_field": ref[0],
                }
    return mappings


def extract_associations(elements: Dict[str, Any], mixin: Optional[Dict[str, Any]] = None) -> List[AssociationMetadata]:
    """Extract associations defined in elements and mixin."""
    associations: List[AssociationMetadata] = []
    seen: Set[str] = set()

    # Associations from elements
    if isinstance(elements, dict):
        for el_name, el_val in elements.items():
            if not isinstance(el_val, dict):
                continue
            el_type = el_val.get("type")
            target = el_val.get("target")
            if el_type == "cds.Association" or target:
                label = get_first_annotation(el_val, "@EndUserText.label", "label")
                cardinality = safe_get(el_val, "cardinality", "max")
                associations.append(
                    AssociationMetadata(
                        name=el_name,
                        target=str(target) if target else "Unknown",
                        cardinality=str(cardinality) if cardinality is not None else None,
                        relationship_type="ASSOCIATION",
                        label=str(label) if label else None,
                        on_condition=el_val.get("on"),
                    )
                )
                seen.add(el_name)

    # Associations from query mixin
    if isinstance(mixin, dict):
        for mix_name, mix_val in mixin.items():
            if mix_name in seen or not isinstance(mix_val, dict):
                continue
            target = mix_val.get("target")
            if target:
                label = get_first_annotation(mix_val, "@EndUserText.label", "label")
                cardinality = safe_get(mix_val, "cardinality", "max")
                associations.append(
                    AssociationMetadata(
                        name=mix_name,
                        target=str(target),
                        cardinality=str(cardinality) if cardinality is not None else None,
                        relationship_type="ASSOCIATION",
                        label=str(label) if label else None,
                        on_condition=mix_val.get("on"),
                    )
                )
                seen.add(mix_name)

    return associations


def extract_hierarchies(entity_data: Dict[str, Any]) -> List[HierarchyMetadata]:
    """Extract @Hierarchy.leveled or other hierarchy definitions."""
    hierarchies: List[HierarchyMetadata] = []
    leveled = get_first_annotation(entity_data, "@Hierarchy.leveled", "@Hierarchy.parentChild")
    if isinstance(leveled, list):
        for h in leveled:
            if not isinstance(h, dict):
                continue
            name = h.get("name", "Unnamed Hierarchy")
            label = h.get("label", name)
            levels: List[str] = []
            for lvl in h.get("levels", []):
                if isinstance(lvl, dict):
                    el = lvl.get("element")
                    if isinstance(el, dict) and "=" in el:
                        levels.append(str(el["="]))
                    elif isinstance(el, str):
                        levels.append(el)
                elif isinstance(lvl, str):
                    levels.append(lvl)
            hierarchies.append(HierarchyMetadata(name=name, label=label, levels=levels))
    return hierarchies


def extract_fields(
    elements: Dict[str, Any],
    bld_attributes: Optional[Dict[str, Any]] = None,
    bld_measures: Optional[Dict[str, Any]] = None,
    field_mappings: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Tuple[List[FieldMetadata], List[FieldMetadata]]:
    """Extract standard fields and measures."""
    fields: List[FieldMetadata] = []
    measures: List[FieldMetadata] = []
    seen: Set[str] = set()

    bld_attr = bld_attributes or {}
    bld_meas = bld_measures or {}
    field_maps = field_mappings or {}

    if isinstance(elements, dict):
        for el_name, el_val in elements.items():
            if not isinstance(el_val, dict):
                continue
            # Skip pure associations
            if el_val.get("type") == "cds.Association":
                continue

            label = get_first_annotation(el_val, "@EndUserText.label") or safe_get(bld_attr, el_name, "text")
            f_type = el_val.get("type")
            native_type = get_first_annotation(el_val, "@DataWarehouse.native.dataType")
            key = bool(el_val.get("key", False))
            not_null = bool(el_val.get("notNull", False))

            # Measure detection
            agg = get_first_annotation(el_val, "@Aggregation.default")
            measure_type = get_first_annotation(el_val, "@AnalyticsDetails.measureType", "@Analytics.Measure")
            is_measure = (agg is not None) or (measure_type is not None) or (el_name in bld_meas)

            if el_name in bld_meas:
                m_info = bld_meas[el_name]
                if isinstance(m_info, dict):
                    if not agg:
                        agg = "SUM"  # Default analytical aggregation
                    if not measure_type:
                        measure_type = m_info.get("measureType", "FactSourceMeasure")
                    if not label:
                        label = m_info.get("text")

            fk_assoc = get_first_annotation(el_val, "@ObjectModel.foreignKey.association")
            if isinstance(fk_assoc, dict) and "=" in fk_assoc:
                fk_assoc = fk_assoc["="]

            nav_ref = el_val.get("@Analytics.navigationAttributeRef")
            if isinstance(nav_ref, list):
                nav_ref = [str(x) for x in nav_ref]

            length = el_val.get("length")
            precision = el_val.get("precision")
            scale = el_val.get("scale")

            source_map = field_maps.get(el_name)

            f_meta = FieldMetadata(
                name=el_name,
                label=str(label) if label else None,
                type=str(f_type) if f_type else None,
                native_type=str(native_type) if native_type else None,
                key=key,
                nullable=not not_null,
                is_measure=is_measure,
                aggregation=str(agg) if agg else None,
                measure_type=str(measure_type) if measure_type else None,
                foreign_key_association=str(fk_assoc) if fk_assoc else None,
                navigation_attribute_ref=nav_ref,
                length=length,
                precision=precision,
                scale=scale,
                source_mapping=source_map,
            )

            fields.append(f_meta)
            seen.add(el_name)
            if is_measure:
                measures.append(f_meta)

    # In case bld_measures contains measures not in elements
    for m_name, m_val in bld_meas.items():
        if m_name not in seen and isinstance(m_val, dict):
            m_label = m_val.get("text", m_name)
            m_type = m_val.get("measureType", "FactSourceMeasure")
            f_meta = FieldMetadata(
                name=m_name,
                label=m_label,
                type="cds.Decimal",
                is_measure=True,
                aggregation="SUM",
                measure_type=str(m_type),
                source_mapping=field_maps.get(m_name),
            )
            fields.append(f_meta)
            measures.append(f_meta)
            seen.add(m_name)

    return fields, measures
