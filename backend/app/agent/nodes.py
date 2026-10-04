import json
import re
from typing import Any, Dict, List, Optional, Tuple
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from app.agent.state import AgentState
from app.agent.tools import (
    get_field_lineage,
    get_field_metadata,
    get_impact_analysis,
    get_lineage,
    get_object_metadata,
    get_objects,
    resolve_object_name,
)
from app.services.llm_service import llm_service
from app.services.session_store import session_store

SYSTEM_PROMPT = """You are a SAP Datasphere metadata assistant.
You answer questions using ONLY information available from the parsed Datasphere CSN metadata provided in the tool results.
The metadata graph is the absolute source of truth.
Rules:
1. Never invent metadata, objects, fields, measures, or relationships.
2. If the requested information is not available in the tool results, explicitly state that it is not present in the parsed CSN.
3. Keep answers concise, direct, and structured with Markdown tables and bullet points where helpful.
4. Clearly distinguish deterministic metadata from reasoning.
5. Emphasize measures and aggregations accurately (e.g. SUM, COUNT).
"""


def extract_entities_from_query(query: str, session_id: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract object and field names from the user query."""
    session = session_store.get_session(session_id)
    if not session:
        return None, None

    query_lower = query.lower()

    # 1. Match known objects (exact or normalized)
    found_object: Optional[str] = None
    for obj in session.parsed_csn.objects:
        obj_name_lower = obj.name.lower()
        obj_label_lower = obj.label.lower() if obj.label else ""

        # Check for word boundary or direct occurrence
        if obj_name_lower in query_lower:
            found_object = obj.name
            break
        if obj_label_lower and len(obj_label_lower) > 3 and obj_label_lower in query_lower:
            found_object = obj.name
            break
        # Match with underscores replaced by spaces
        if obj.name.replace("_", " ").lower() in query_lower:
            found_object = obj.name
            break

    # Preserve an explicitly named, unknown object so deterministic tools can
    # return a precise "not present in CSN" result instead of listing objects.
    if not found_object:
        requested_name = re.search(
            r"(?:\b(?:of|for|on|about|object|entity)\b)\s+([A-Za-z][A-Za-z0-9_.-]*)",
            query,
            flags=re.IGNORECASE,
        )
        if requested_name:
            candidate = requested_name.group(1).rstrip("?,.!:;")
            if candidate.lower() not in {"the", "this", "that", "its"}:
                found_object = candidate

    # 2. Match known fields
    found_field: Optional[str] = None
    all_fields: Dict[str, str] = {}
    for obj in session.parsed_csn.objects:
        for f in obj.fields:
            all_fields[f.name.lower()] = f.name

    for f_lower, f_name in all_fields.items():
        pattern = r"\b" + re.escape(f_lower) + r"\b"
        if re.search(pattern, query_lower):
            found_field = f_name
            break

    # If no object was explicitly found, but a field was found and it exists in a specific object
    if not found_object and found_field:
        for obj in session.parsed_csn.objects:
            if any(f.name == found_field for f in obj.fields):
                # We can keep found_object None to search across all, or set it
                pass

    return found_object, found_field


def route_intent(query: str, found_object: Optional[str], found_field: Optional[str]) -> Tuple[str, Dict[str, Any]]:
    """Determine which deterministic tool to call and with what parameters."""
    q = query.lower()

    # Lineage intents
    if any(k in q for k in ["lineage", "where does", "upstream", "downstream", "flow from", "source of"]):
        if found_object and found_field and "field" in q:
            return "get_field_lineage", {"object_name": found_object, "field_name": found_field}
        if found_object:
            return "get_lineage", {"object_name": found_object}

    # Impact intents
    if any(k in q for k in ["impact", "what happens if", "what depends on", "affected if", "modify", "changes", "break"]):
        if found_object:
            return "get_impact_analysis", {"object_name": found_object}

    # Field specific intents (measure, aggregation, field info)
    if found_field and any(k in q for k in ["measure", "aggregation", "field", "what is " + found_field.lower(), "datatype", "type of " + found_field.lower()]):
        return "get_field_metadata", {"object_name": found_object, "field_name": found_field}

    # General list objects intent
    if any(k in q for k in ["all objects", "list objects", "show objects", "what objects", "show all", "list of objects"]):
        return "get_objects", {}

    # Object metadata intent
    if found_object:
        return "get_object_metadata", {"object_name": found_object}

    # If a field was identified
    if found_field:
        return "get_field_metadata", {"object_name": found_object, "field_name": found_field}

    # Fallback default: list available objects
    return "get_objects", {}


def format_deterministic_answer(tool_name: str, tool_result: Dict[str, Any], query: str) -> str:
    """Format tool results into a rich, clear response when running in fallback mode or small LLM."""
    if "error" in tool_result:
        return f"⚠️ **Not Found in CSN:** {tool_result['error']}"

    if tool_name == "get_objects":
        objects = tool_result.get("objects", [])
        md = f"### 📦 Available Datasphere Objects ({len(objects)})\n\n"
        md += "| Object Name | Modeling Pattern / Kind | Measures | Fields | Label |\n"
        md += "| :--- | :--- | :--- | :--- | :--- |\n"
        for obj in objects:
            pattern = obj.get("type") or "ENTITY"
            label = obj.get("label") or "-"
            md += f"| **`{obj['name']}`** | `{pattern}` | {obj['measure_count']} | {obj['field_count']} | {label} |\n"
        return md

    if tool_name == "get_object_metadata":
        name = tool_result.get("name")
        label = tool_result.get("label")
        pattern = tool_result.get("type")
        sources = tool_result.get("source_objects", [])
        fields = tool_result.get("fields", [])
        measures = tool_result.get("measures", [])
        assocs = tool_result.get("associations", [])
        hierarchies = tool_result.get("hierarchies", [])

        md = f"### 🔍 Object: `{name}`\n\n"
        md += f"- **Label:** {label}\n"
        md += f"- **Modeling Pattern:** `{pattern}`\n"
        if sources:
            md += f"- **Direct Upstream Sources:** {', '.join([f'`{s}`' for s in sources])}\n"
        else:
            md += f"- **Direct Upstream Sources:** None (Base table or root entity)\n"

        if measures:
            md += f"\n#### 📊 Measures ({len(measures)})\n"
            for m in measures:
                md += f"- **`{m['name']}`** ({m.get('label') or 'Measure'}): Aggregation: **`{m.get('aggregation') or 'SUM'}`**\n"

        md += f"\n#### 📋 Fields ({len(fields)})\n"
        md += "| Field | Type | Key | Measure | Aggregation |\n| :--- | :--- | :--- | :--- | :--- |\n"
        for f in fields[:15]:  # Show first 15 for brevity
            k = "🔑 Yes" if f.get("key") else "No"
            meas = "✅ Yes" if f.get("is_measure") else "No"
            agg = f"`{f.get('aggregation')}`" if f.get("aggregation") else "-"
            md += f"| `{f['name']}` | `{f.get('type') or '-'}` | {k} | {meas} | {agg} |\n"
        if len(fields) > 15:
            md += f"\n*(Showing 15 of {len(fields)} fields)*\n"

        if assocs:
            md += f"\n#### 🔗 Associations ({len(assocs)})\n"
            for a in assocs:
                md += f"- `{a['name']}` ➔ Target: **`{a['target']}`** ({a.get('relationship_type')})\n"

        if hierarchies:
            md += f"\n#### 🌲 Hierarchies\n"
            for h in hierarchies:
                md += f"- **{h.get('label') or h.get('name')}**: {' ➔ '.join(h.get('levels', []))}\n"

        return md

    if tool_name == "get_lineage":
        obj = tool_result.get("object")
        upstream = tool_result.get("upstream", [])
        downstream = tool_result.get("downstream", [])
        direct_sources = tool_result.get("direct_sources", [])

        md = f"### 🔄 Lineage for `{obj}`\n\n"
        if direct_sources:
            md += f"**Direct Sources:** {', '.join([f'`{s}`' for s in direct_sources])}\n\n"
        if upstream:
            md += f"**All Upstream Dependencies ({len(upstream)}):**\n"
            for u in upstream:
                md += f"- ⬆️ `{u}`\n"
        else:
            md += "No upstream dependencies (this is a root data source entity).\n"

        if downstream:
            md += f"\n**Downstream Consumers ({len(downstream)}):**\n"
            for d in downstream:
                md += f"- ⬇️ `{d}`\n"
        else:
            md += "\nNo downstream dependents found (this is an end-consumption analytical model or leaf object).\n"

        return md

    if tool_name == "get_impact_analysis":
        target = tool_result.get("target_object")
        severity = tool_result.get("severity", "LOW")
        affected_count = tool_result.get("affected_count", 0)
        direct = tool_result.get("direct_dependents", [])
        downstream = tool_result.get("downstream_dependents", [])
        details = tool_result.get("details", [])

        sev_color = "🔴" if severity == "CRITICAL" else ("🟠" if severity == "HIGH" else "🟡")
        md = f"### ⚠️ Impact Analysis for `{target}`\n\n"
        md += f"**Risk Level:** {sev_color} **{severity}** (Impacts {affected_count} downstream object(s))\n\n"

        if direct:
            md += f"**Direct Dependents ({len(direct)}):**\n"
            for d in direct:
                md += f"- ⚠️ `{d}`\n"

        if len(downstream) > len(direct):
            indirect = [x for x in downstream if x not in direct]
            md += f"\n**Transitive Downstream Dependents:**\n"
            for ind in indirect:
                md += f"- 🔸 `{ind}`\n"

        if details:
            md += "\n**Impact Summary:**\n"
            for det in details:
                md += f"- {det}\n"

        return md

    if tool_name == "get_field_metadata":
        if "occurrences" in tool_result:
            occs = tool_result.get("occurrences", [])
            f_name = tool_result.get("field")
            md = f"### 🏷️ Field Metadata: `{f_name}`\n\n"
            for occ in occs:
                meas = "Yes (Measure)" if occ.get("is_measure") else "No"
                agg = occ.get("aggregation") or "None"
                md += f"**In Object `{occ['object']}`:**\n"
                md += f"- **Type:** `{occ.get('type')}` (Native: `{occ.get('native_type') or '-'}`)\n"
                md += f"- **Label:** {occ.get('label') or '-'}\n"
                md += f"- **Key Field:** {'Yes' if occ.get('key') else 'No'}\n"
                md += f"- **Is Measure:** {meas}\n"
                md += f"- **Aggregation:** `{agg}`\n"
                if occ.get("foreign_key_association"):
                    md += f"- **Foreign Key Association:** `{occ['foreign_key_association']}`\n"
                md += "\n"
            return md
        else:
            obj = tool_result.get("object")
            f_name = tool_result.get("field")
            meas = "Yes (Measure)" if tool_result.get("is_measure") else "No"
            agg = tool_result.get("aggregation") or "None"
            md = f"### 🏷️ Field `{f_name}` in `{obj}`\n\n"
            md += f"- **Label:** {tool_result.get('label') or '-'}\n"
            md += f"- **Type:** `{tool_result.get('type')}`\n"
            md += f"- **Key Field:** {'Yes' if tool_result.get('key') else 'No'}\n"
            md += f"- **Is Measure:** {meas}\n"
            md += f"- **Aggregation:** `{agg}`\n"
            return md

    if tool_name == "get_field_lineage":
        status = tool_result.get("status")
        f_name = tool_result.get("field_name")
        obj = tool_result.get("object_name")
        hops = tool_result.get("hops", [])
        reason = tool_result.get("reason")

        md = f"### 🧭 Field Lineage: `{obj}.{f_name}`\n\n"
        if status == "resolved":
            md += f"**Origin:** `{tool_result.get('source_entity')}.{tool_result.get('source_field')}`\n\n"
            md += "**Lineage Trace:**\n"
            for i, h in enumerate(hops):
                meas_info = f" (Measure, Agg: {h.get('aggregation')})" if h.get("is_measure") else ""
                md += f"{i+1}. `{h['entity']}` ➔ Field: `{h['field']}`{meas_info}\n"
        elif status == "source_origin":
            md += f"This field originates directly in base entity `{obj}`.\n"
        else:
            md += f"Status: **Unknown**\n\n"
            if reason:
                md += f"Reason: {reason}\n"
        return md

    return json.dumps(tool_result, indent=2)


def tool_execution_node(state: AgentState) -> AgentState:
    """Executes the deterministic tool selected for the query."""
    user_query = state["user_query"]
    session_id = state["session_id"]

    found_obj, found_field = extract_entities_from_query(user_query, session_id)
    tool_name, tool_args = route_intent(user_query, found_obj, found_field)

    result: Dict[str, Any] = {}
    sources: List[Dict[str, Any]] = []

    if tool_name == "get_objects":
        result = get_objects(session_id)
        sources.append({"type": "objects_list", "count": result.get("count", 0)})

    elif tool_name == "get_object_metadata":
        obj_name = tool_args.get("object_name", "")
        result = get_object_metadata(session_id, obj_name)
        sources.append({"type": "metadata", "object": obj_name})

    elif tool_name == "get_lineage":
        obj_name = tool_args.get("object_name", "")
        result = get_lineage(session_id, obj_name)
        sources.append({"type": "lineage", "object": obj_name})

    elif tool_name == "get_impact_analysis":
        obj_name = tool_args.get("object_name", "")
        result = get_impact_analysis(session_id, obj_name)
        sources.append({"type": "impact", "object": obj_name})

    elif tool_name == "get_field_metadata":
        obj_name = tool_args.get("object_name")
        field_name = tool_args.get("field_name", "")
        result = get_field_metadata(session_id, obj_name, field_name)
        sources.append({"type": "field_metadata", "field": field_name, "object": obj_name})

    elif tool_name == "get_field_lineage":
        obj_name = tool_args.get("object_name", "")
        field_name = tool_args.get("field_name", "")
        result = get_field_lineage(session_id, obj_name, field_name)
        sources.append({"type": "field_lineage", "field": field_name, "object": obj_name})

    state["tool_results"] = {tool_name: result}
    state["tools_used"] = [tool_name]
    state["sources"] = sources
    return state


def agent_response_node(state: AgentState) -> AgentState:
    """Uses LLM (if configured) or deterministic template to synthesize final response."""
    tool_results = state.get("tool_results", {})
    tools_used = state.get("tools_used", [])
    user_query = state["user_query"]
    session_id = state["session_id"]

    if not tools_used:
        state["final_answer"] = "No applicable deterministic tool could be run for this query."
        return state

    tool_name = tools_used[0]
    result_data = tool_results.get(tool_name, {})

    llm = llm_service.get_llm()

    # If LLM is configured and operational, let the LLM format the answer based strictly on tool results
    if llm:
        try:
            prompt_content = f"""User Question: {user_query}
Deterministic Tool Used: {tool_name}
Deterministic Tool Output:
{json.dumps(result_data, indent=2)}

Please provide a clear, accurate, and concise answer based ONLY on the deterministic tool output above.
Do not invent any information. Follow the system rules."""

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt_content),
            ]
            response: AIMessage = llm.invoke(messages)
            state["final_answer"] = str(response.content)
            return state
        except Exception as e:
            # Fall back to deterministic markdown formatter
            pass

    # Deterministic fallback mode (100% reliable, zero hallucination, instant)
    formatted = format_deterministic_answer(tool_name, result_data, user_query)
    state["final_answer"] = formatted
    return state
