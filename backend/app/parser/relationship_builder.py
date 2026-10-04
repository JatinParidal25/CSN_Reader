from typing import Any, Dict, List, Set, Tuple
from app.models.metadata_models import AssociationMetadata, ObjectMetadata, Relationship


class RelationshipBuilder:
    """
    Builds deterministic relationships between Datasphere objects.
    Captures:
    - Direct query sources (e.g. from / join)
    - Fact and Dimension sources from Analytic Models
    - Element and Mixin associations
    - Foreign key association links
    """

    @staticmethod
    def build_relationships(objects: List[ObjectMetadata]) -> List[Relationship]:
        relationships: List[Relationship] = []
        known_objects: Set[str] = {obj.name for obj in objects}
        seen_edges: Set[Tuple[str, str, str, str]] = set()

        for obj in objects:
            source_name = obj.name

            # 1. Query and Fact Sources
            for src_obj in obj.source_objects:
                # If src_obj is known or is a valid entity reference
                rel_type = "FACT_SOURCE" if obj.modeling_pattern == "ANALYTICAL_CUBE" else "SOURCE"
                edge_key = (source_name, src_obj, rel_type, "")
                if edge_key not in seen_edges and src_obj != source_name:
                    relationships.append(
                        Relationship(
                            source=source_name,
                            target=src_obj,
                            relationship_type=rel_type,
                            metadata={"category": "data_flow"},
                        )
                    )
                    seen_edges.add(edge_key)

            # 2. Associations
            for assoc in obj.associations:
                target_entity = assoc.target
                if not target_entity or target_entity in ("Unknown", source_name):
                    continue

                rel_type = "ASSOCIATION"
                edge_key = (source_name, target_entity, rel_type, assoc.name)
                if edge_key not in seen_edges:
                    relationships.append(
                        Relationship(
                            source=source_name,
                            target=target_entity,
                            relationship_type=rel_type,
                            field=assoc.name,
                            metadata={
                                "cardinality": assoc.cardinality,
                                "label": assoc.label,
                                "on_condition": assoc.on_condition,
                            },
                        )
                    )
                    seen_edges.add(edge_key)

            # 3. Foreign key associations on fields
            for field in obj.fields:
                if field.foreign_key_association:
                    # Find association target matching this association name
                    matched_target = None
                    for assoc in obj.associations:
                        if assoc.name == field.foreign_key_association:
                            matched_target = assoc.target
                            break

                    if matched_target and matched_target != source_name:
                        edge_key = (source_name, matched_target, "FOREIGN_KEY", field.name)
                        if edge_key not in seen_edges:
                            relationships.append(
                                Relationship(
                                    source=source_name,
                                    target=matched_target,
                                    relationship_type="FOREIGN_KEY",
                                    field=field.name,
                                    metadata={
                                        "association_name": field.foreign_key_association,
                                        "field_name": field.name,
                                    },
                                )
                            )
                            seen_edges.add(edge_key)

        return relationships
