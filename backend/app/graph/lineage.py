from typing import Any, Dict, List, Optional, Set
import networkx as nx
from app.graph.metadata_graph import MetadataGraph
from app.models.api_models import (
    FieldLineageResponse,
    ImpactResponse,
    LineageEdge,
    LineageNode,
    LineageResponse,
)


class LineageEngine:
    """
    Deterministic Lineage Engine for SAP Datasphere metadata.
    Computes upstream/downstream object lineage, impact analysis, and field-level tracing
    without LLM inference.
    """

    def __init__(self, metadata_graph: MetadataGraph):
        self.meta_graph = metadata_graph
        self.g = metadata_graph.graph

    def get_object_lineage(self, object_name: str) -> LineageResponse:
        """
        Compute upstream sources and downstream consumers for an object,
        along with the complete visual subgraph.
        """
        if not self.g.has_node(object_name):
            return LineageResponse(
                object_name=object_name,
                upstream=[],
                downstream=[],
                nodes=[],
                edges=[],
            )

        all_upstream = self.meta_graph.get_all_upstream(object_name)
        all_downstream = self.meta_graph.get_all_downstream(object_name)

        # Build subgraph containing object_name, all upstream, and all downstream
        subgraph_nodes_set: Set[str] = {object_name}.union(all_upstream).union(all_downstream)
        subgraph = self.g.subgraph(subgraph_nodes_set)

        nodes: List[LineageNode] = []
        for n in subgraph.nodes():
            node_data = self.g.nodes[n]
            obj = self.meta_graph.get_object(n)
            label = node_data.get("label", n)
            pattern = obj.modeling_pattern if obj else node_data.get("modeling_pattern")
            kind = obj.kind if obj else node_data.get("kind", "entity")
            nodes.append(
                LineageNode(
                    id=n,
                    label=label,
                    kind=kind,
                    modeling_pattern=pattern,
                    is_current=(n == object_name),
                )
            )

        edges: List[LineageEdge] = []
        for u, v, data in subgraph.edges(data=True):
            rel_type = data.get("relationship_type", "DEPENDS_ON")
            field = data.get("field")
            edges.append(
                LineageEdge(
                    source=u,
                    target=v,
                    relationship_type=rel_type,
                    label=field or rel_type,
                )
            )

        return LineageResponse(
            object_name=object_name,
            upstream=all_upstream,
            downstream=all_downstream,
            nodes=nodes,
            edges=edges,
        )

    def get_upstream_dependencies(self, object_name: str) -> List[str]:
        return self.meta_graph.get_all_upstream(object_name)

    def get_downstream_dependencies(self, object_name: str) -> List[str]:
        return self.meta_graph.get_all_downstream(object_name)

    def get_impact_analysis(self, object_name: str) -> ImpactResponse:
        """
        Deterministic impact analysis if object_name is modified, renamed, or deleted.
        Calculates direct dependents, all downstream dependents, upstream prerequisites,
        and assigns a severity score.
        """
        if not self.g.has_node(object_name):
            return ImpactResponse(
                target_object=object_name,
                direct_dependents=[],
                downstream_dependents=[],
                upstream_prerequisites=[],
                affected_count=0,
                severity="LOW",
                details=[f"Object '{object_name}' was not found in the parsed CSN graph."],
            )

        direct_dependents = self.meta_graph.get_direct_downstream(object_name)
        all_downstream = self.meta_graph.get_all_downstream(object_name)
        all_upstream = self.meta_graph.get_all_upstream(object_name)

        affected_count = len(all_downstream)

        # Severity determination
        if affected_count >= 4 or any(
            self.meta_graph.get_object(d) and self.meta_graph.get_object(d).modeling_pattern == "ANALYTICAL_CUBE"
            for d in all_downstream
        ):
            severity = "CRITICAL" if affected_count >= 5 else "HIGH"
        elif affected_count > 1:
            severity = "MEDIUM"
        elif affected_count == 1:
            severity = "LOW"
        else:
            severity = "LOW"

        details: List[str] = []
        if affected_count == 0:
            details.append(
                f"Modifying '{object_name}' has minimal or localized impact; no downstream analytical models or views depend on it."
            )
        else:
            details.append(
                f"Modifying '{object_name}' will directly affect {len(direct_dependents)} object(s): {', '.join(direct_dependents)}."
            )
            if len(all_downstream) > len(direct_dependents):
                indirect = [d for d in all_downstream if d not in direct_dependents]
                details.append(
                    f"Transitively affects {len(indirect)} additional downstream consumer(s): {', '.join(indirect)}."
                )

        affected_fields: Dict[str, List[str]] = {}
        target_obj = self.meta_graph.get_object(object_name)
        if target_obj:
            field_names = [f.name for f in target_obj.fields]
            for dep in direct_dependents:
                dep_obj = self.meta_graph.get_object(dep)
                if dep_obj:
                    common_fields = [f.name for f in dep_obj.fields if f.name in field_names]
                    if common_fields:
                        affected_fields[dep] = common_fields

        return ImpactResponse(
            target_object=object_name,
            direct_dependents=direct_dependents,
            downstream_dependents=all_downstream,
            upstream_prerequisites=all_upstream,
            affected_count=affected_count,
            severity=severity,
            details=details,
            affected_fields=affected_fields,
        )

    def get_field_lineage(self, object_name: str, field_name: str) -> FieldLineageResponse:
        """
        Deterministic field-level lineage. Traces where a field originates.
        """
        obj = self.meta_graph.get_object(object_name)
        if not obj:
            return FieldLineageResponse(
                object_name=object_name,
                field_name=field_name,
                status="unknown",
                reason=f"Object '{object_name}' does not exist in the parsed metadata.",
            )

        # Find field
        field_meta = next((f for f in obj.fields if f.name == field_name), None)
        if not field_meta:
            return FieldLineageResponse(
                object_name=object_name,
                field_name=field_name,
                status="unknown",
                reason=f"Field '{field_name}' not found on object '{object_name}'.",
            )

        hops: List[Dict[str, Any]] = [
            {
                "entity": object_name,
                "field": field_name,
                "type": field_meta.type,
                "is_measure": field_meta.is_measure,
                "aggregation": field_meta.aggregation,
            }
        ]

        curr_entity = object_name
        curr_field = field_meta
        visited: Set[str] = {f"{object_name}.{field_name}"}

        while curr_field and curr_field.source_mapping:
            src_ent = curr_field.source_mapping.get("source_entity")
            src_fld = curr_field.source_mapping.get("source_field")

            # If source_entity not specified in mapping, check direct sources of curr_entity
            if not src_ent:
                parent_obj = self.meta_graph.get_object(curr_entity)
                if parent_obj and len(parent_obj.source_objects) == 1:
                    src_ent = parent_obj.source_objects[0]

            if not src_ent or not src_fld:
                break

            hop_key = f"{src_ent}.{src_fld}"
            if hop_key in visited:
                break
            visited.add(hop_key)

            src_obj = self.meta_graph.get_object(src_ent)
            src_field_meta = next((f for f in src_obj.fields if f.name == src_fld), None) if src_obj else None

            hops.append(
                {
                    "entity": src_ent,
                    "field": src_fld,
                    "type": src_field_meta.type if src_field_meta else None,
                    "is_measure": src_field_meta.is_measure if src_field_meta else False,
                    "aggregation": src_field_meta.aggregation if src_field_meta else None,
                }
            )

            curr_entity = src_ent
            curr_field = src_field_meta

        # Check navigationAttributeRef e.g. ["_FKDAT", "MONTH"]
        if field_meta.navigation_attribute_ref and len(field_meta.navigation_attribute_ref) >= 2:
            assoc_name = field_meta.navigation_attribute_ref[0]
            target_field = field_meta.navigation_attribute_ref[1]
            assoc = next((a for a in obj.associations if a.name == assoc_name), None)
            if assoc and assoc.target:
                hops.append(
                    {
                        "entity": assoc.target,
                        "field": target_field,
                        "relationship": f"Navigation attribute via association '{assoc_name}'",
                    }
                )
                return FieldLineageResponse(
                    object_name=object_name,
                    field_name=field_name,
                    status="resolved",
                    source_entity=assoc.target,
                    source_field=target_field,
                    hops=hops,
                )

        if len(hops) > 1:
            origin = hops[-1]
            return FieldLineageResponse(
                object_name=object_name,
                field_name=field_name,
                status="resolved",
                source_entity=origin["entity"],
                source_field=origin["field"],
                hops=hops,
            )

        # If it's a base table (no source objects)
        if not obj.source_objects:
            return FieldLineageResponse(
                object_name=object_name,
                field_name=field_name,
                status="source_origin",
                source_entity=object_name,
                source_field=field_name,
                hops=hops,
                reason=f"Field '{field_name}' originates directly in source entity '{object_name}'.",
            )

        return FieldLineageResponse(
            object_name=object_name,
            field_name=field_name,
            status="unknown",
            hops=hops,
            reason="The CSN does not provide sufficient field-level mapping information for this field.",
        )
