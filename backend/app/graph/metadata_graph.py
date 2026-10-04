from typing import Any, Dict, List, Optional, Set
import networkx as nx
from app.models.metadata_models import ObjectMetadata, ParsedCSN, Relationship


class MetadataGraph:
    """
    In-memory directed metadata graph for SAP Datasphere objects.
    Enables deterministic lineage queries, dependency traversal, and impact analysis.
    """

    def __init__(self, parsed_csn: ParsedCSN):
        self.parsed_csn = parsed_csn
        self.objects_by_name: Dict[str, ObjectMetadata] = {
            obj.name: obj for obj in parsed_csn.objects
        }
        # In this graph, an edge (consumer, dependency) means consumer depends on dependency.
        # Edge: A -> B means A consumes/references/sources B.
        self.graph = nx.DiGraph()
        self._build_graph()

    def _build_graph(self) -> None:
        # Add all nodes
        for name, obj in self.objects_by_name.items():
            self.graph.add_node(
                name,
                label=obj.label or name,
                kind=obj.kind,
                modeling_pattern=obj.modeling_pattern,
                measures_count=len(obj.measures),
                fields_count=len(obj.fields),
            )

        # Add relationships as edges: consumer -> dependency
        for rel in self.parsed_csn.relationships:
            if not self.graph.has_node(rel.target):
                # Target might be an external entity or standard context table like SAP.TIME.M_TIME_DIMENSION
                self.graph.add_node(
                    rel.target,
                    label=rel.target,
                    kind="external_or_context",
                    modeling_pattern="ENTITY",
                    measures_count=0,
                    fields_count=0,
                )

            # Avoid adding multiple duplicate edges with same type
            self.graph.add_edge(
                rel.source,
                rel.target,
                relationship_type=rel.relationship_type,
                field=rel.field,
                metadata=rel.metadata,
            )

    def get_object(self, name: str) -> Optional[ObjectMetadata]:
        return self.objects_by_name.get(name)

    def list_objects(self) -> List[ObjectMetadata]:
        return list(self.objects_by_name.values())

    def get_direct_upstream(self, object_name: str) -> List[str]:
        """Objects that object_name directly sources from or associates with."""
        if not self.graph.has_node(object_name):
            return []
        return sorted(list(self.graph.successors(object_name)))

    def get_all_upstream(self, object_name: str) -> List[str]:
        """All transitive objects that object_name relies upon."""
        if not self.graph.has_node(object_name):
            return []
        return sorted(list(nx.descendants(self.graph, object_name)))

    def get_direct_downstream(self, object_name: str) -> List[str]:
        """Objects that directly consume or reference object_name."""
        if not self.graph.has_node(object_name):
            return []
        return sorted(list(self.graph.predecessors(object_name)))

    def get_all_downstream(self, object_name: str) -> List[str]:
        """All transitive objects that consume or depend on object_name."""
        if not self.graph.has_node(object_name):
            return []
        return sorted(list(nx.ancestors(self.graph, object_name)))
