export interface FieldMetadata {
  name: string;
  label?: string | null;
  type?: string | null;
  native_type?: string | null;
  key: boolean;
  nullable: boolean;
  is_measure: boolean;
  aggregation?: string | null;
  measure_type?: string | null;
  foreign_key_association?: string | null;
  navigation_attribute_ref?: string[] | null;
  length?: number | null;
  precision?: number | null;
  scale?: number | null;
}

export interface AssociationMetadata {
  name: string;
  target: string;
  cardinality?: string | null;
  relationship_type: string;
  label?: string | null;
  on_condition?: any;
}

export interface HierarchyMetadata {
  name: string;
  label?: string | null;
  levels: string[];
}

export interface ObjectMetadata {
  name: string;
  label?: string | null;
  kind: string;
  modeling_pattern?: string | null;
  supported_capabilities: string[];
  source_objects: string[];
  fields: FieldMetadata[];
  measures: FieldMetadata[];
  associations: AssociationMetadata[];
  hierarchies: HierarchyMetadata[];
  annotations: Record<string, any>;
  folder_assignment?: string | null;
  description?: string | null;
}

export interface Relationship {
  source: string;
  target: string;
  relationship_type: string;
  field?: string | null;
  metadata?: Record<string, any>;
}

export interface ParsedCSN {
  filename: string;
  version?: string | null;
  objects: ObjectMetadata[];
  relationships: Relationship[];
  object_count: number;
  relationship_count: number;
  field_count: number;
  measure_count: number;
}

export interface UploadResponse {
  success: boolean;
  session_id: string;
  filename: string;
  object_count: number;
  relationship_count: number;
  field_count: number;
  measure_count: number;
  message: string;
}

export interface LineageNode {
  id: string;
  label: string;
  kind?: string | null;
  modeling_pattern?: string | null;
  is_current: boolean;
}

export interface LineageEdge {
  source: string;
  target: string;
  relationship_type: string;
  label?: string | null;
}

export interface LineageResponse {
  object_name: string;
  upstream: string[];
  downstream: string[];
  nodes: LineageNode[];
  edges: LineageEdge[];
  field_lineage?: any;
}

export interface ImpactResponse {
  target_object: string;
  direct_dependents: string[];
  downstream_dependents: string[];
  upstream_prerequisites: string[];
  affected_count: number;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  details: string[];
  affected_fields: Record<string, string[]>;
}

export interface FieldLineageResponse {
  object_name: string;
  field_name: string;
  status: string;
  source_entity?: string | null;
  source_field?: string | null;
  hops: Array<{
    entity: string;
    field: string;
    type?: string | null;
    is_measure?: boolean;
    aggregation?: string | null;
    relationship?: string;
  }>;
  reason?: string | null;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  tools_used?: string[];
  sources?: any[];
  timestamp: string;
}

export interface ChatResponse {
  answer: string;
  tools_used: string[];
  sources: any[];
}
