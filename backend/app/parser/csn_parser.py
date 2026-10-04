import json
from typing import Any, Dict, List, Optional, Set
from app.models.metadata_models import (
    AssociationMetadata,
    FieldMetadata,
    ObjectMetadata,
    ParsedCSN,
)
from app.parser.metadata_extractor import (
    extract_associations,
    extract_field_source_mappings,
    extract_fields,
    extract_hierarchies,
    extract_query_sources,
    get_first_annotation,
    safe_get,
    unwrap_annotation_value,
)
from app.parser.relationship_builder import RelationshipBuilder


class CSNParser:
    """
    Deterministic SAP Datasphere CSN / JSON Parser.
    Extracts entities, analytic models, fields, measures, hierarchies, associations,
    and constructs a normalized metadata graph.
    """

    def __init__(self):
        pass

    def parse(self, content: Any, filename: str = "csn.json") -> ParsedCSN:
        """Parse raw JSON string, bytes, or dictionary."""
        if isinstance(content, (str, bytes)):
            try:
                data = json.loads(content)
            except Exception as e:
                raise ValueError(f"Invalid JSON content: {str(e)}")
        elif isinstance(content, dict):
            data = content
        else:
            raise ValueError(f"Expected string, bytes, or dict, got {type(content)}")

        if not isinstance(data, dict):
            raise ValueError("Root CSN structure must be a JSON object")

        definitions: Dict[str, Any] = data.get("definitions", {})
        business_layers: Dict[str, Any] = data.get("businessLayerDefinitions", {})
        version = safe_get(data, "version", "csn") or data.get("$version") or "2.0"

        # Collect all entity/model names
        all_names: Set[str] = set()
        if isinstance(definitions, dict):
            all_names.update(definitions.keys())
        if isinstance(business_layers, dict):
            all_names.update(business_layers.keys())

        # Exclude internal contexts that have no elements or query
        parsed_objects: List[ObjectMetadata] = []
        all_field_count = 0
        all_measure_count = 0

        for name in all_names:
            def_data = definitions.get(name, {}) if isinstance(definitions, dict) else {}
            bld_data = business_layers.get(name, {}) if isinstance(business_layers, dict) else {}

            kind = def_data.get("kind", "entity")
            # If kind is "context" and has no elements and no query, skip pure namespace contexts
            if kind == "context" and not def_data.get("elements") and not def_data.get("query"):
                continue

            # Determine label
            label = (
                get_first_annotation(def_data, "@EndUserText.label", "label")
                or bld_data.get("text")
                or safe_get(bld_data, "identifier", "text")
                or name
            )

            # Determine modeling pattern
            pattern = get_first_annotation(
                def_data,
                "@ObjectModel.modelingPattern",
                "@DataWarehouse.modelingPattern",
                "@ModelingPattern",
            )
            if not pattern and name in business_layers:
                pattern = "ANALYTICAL_CUBE"
            elif not pattern and def_data.get("query"):
                pattern = "VIEW"
            elif not pattern:
                pattern = "ENTITY"

            # Determine supported capabilities
            caps_raw = get_first_annotation(def_data, "@ObjectModel.supportedCapabilities")
            capabilities: List[str] = []
            if isinstance(caps_raw, list):
                for c in caps_raw:
                    val = unwrap_annotation_value(c)
                    if isinstance(val, str):
                        capabilities.append(val)
            elif isinstance(caps_raw, str):
                capabilities.append(caps_raw)

            # Extract query sources
            source_objects: Set[str] = set()
            query_select = safe_get(def_data, "query", "SELECT")
            if query_select:
                from_node = query_select.get("from")
                found_sources = extract_query_sources(from_node, current_obj_name=name)
                source_objects.update(found_sources)

            # Extract BLD sources (Analytic models)
            source_model = bld_data.get("sourceModel", {})
            if isinstance(source_model, dict):
                fact_sources = source_model.get("factSources", {})
                if isinstance(fact_sources, dict):
                    for fs_key, fs_val in fact_sources.items():
                        entity_key = safe_get(fs_val, "dataEntity", "key")
                        if entity_key:
                            source_objects.add(entity_key)

                dim_sources = source_model.get("dimensionSources", {})
                if isinstance(dim_sources, dict):
                    for ds_key, ds_val in dim_sources.items():
                        dim_entity = safe_get(ds_val, "dataEntity", "key")
                        if dim_entity:
                            source_objects.add(dim_entity)

            # Filter source_objects to valid names (remove self or aliases)
            cleaned_sources = [s for s in sorted(source_objects) if s != name]

            # Field mappings from SELECT columns
            field_mappings = extract_field_source_mappings(query_select) if query_select else {}

            # Elements
            elements = def_data.get("elements", {})
            bld_attributes = bld_data.get("attributes", {})
            bld_measures = bld_data.get("measures", {})

            # Fields and Measures
            fields, measures = extract_fields(
                elements=elements,
                bld_attributes=bld_attributes,
                bld_measures=bld_measures,
                field_mappings=field_mappings,
            )

            all_field_count += len(fields)
            all_measure_count += len(measures)

            # Associations
            mixin = query_select.get("mixin") if query_select else None
            associations = extract_associations(elements=elements, mixin=mixin)

            # Also add dimension sources as associations if not already present
            if isinstance(source_model, dict):
                dim_sources = source_model.get("dimensionSources", {})
                if isinstance(dim_sources, dict):
                    existing_targets = {a.target for a in associations}
                    for ds_key, ds_val in dim_sources.items():
                        dim_entity = safe_get(ds_val, "dataEntity", "key")
                        if dim_entity and dim_entity not in existing_targets:
                            associations.append(
                                AssociationMetadata(
                                    name=ds_key,
                                    target=dim_entity,
                                    relationship_type="DIMENSION_ASSOCIATION",
                                    label=ds_val.get("text", ds_key),
                                )
                            )

            # Hierarchies
            hierarchies = extract_hierarchies(def_data)

            # Folder assignment
            folder = safe_get(def_data, "_meta", "dependencies", "folderAssignment")

            # Collect other annotations
            annotations = {
                k: unwrap_annotation_value(v)
                for k, v in def_data.items()
                if k.startswith("@") and k not in (
                    "@EndUserText.label",
                    "@ObjectModel.modelingPattern",
                    "@ObjectModel.supportedCapabilities",
                    "@Hierarchy.leveled",
                )
            }

            obj = ObjectMetadata(
                name=name,
                label=str(label),
                kind=kind,
                modeling_pattern=str(pattern) if pattern else None,
                supported_capabilities=capabilities,
                source_objects=cleaned_sources,
                fields=fields,
                measures=measures,
                associations=associations,
                hierarchies=hierarchies,
                annotations=annotations,
                folder_assignment=str(folder) if folder else None,
            )
            parsed_objects.append(obj)

        # Sort objects alphabetically by name
        parsed_objects.sort(key=lambda x: x.name)

        # Build relationships
        relationships = RelationshipBuilder.build_relationships(parsed_objects)

        return ParsedCSN(
            filename=filename,
            version=str(version),
            objects=parsed_objects,
            relationships=relationships,
            object_count=len(parsed_objects),
            relationship_count=len(relationships),
            field_count=all_field_count,
            measure_count=all_measure_count,
        )
