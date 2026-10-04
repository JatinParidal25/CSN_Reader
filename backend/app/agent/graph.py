from typing import Any, Dict
from langgraph.graph import END, START, StateGraph
from app.agent.nodes import agent_response_node, tool_execution_node
from app.agent.state import AgentState
from app.models.api_models import ChatResponse


def build_lineage_agent_graph():
    """Build the LangGraph execution graph."""
    workflow = StateGraph(AgentState)

    workflow.add_node("execute_tool", tool_execution_node)
    workflow.add_node("generate_response", agent_response_node)

    workflow.add_edge(START, "execute_tool")
    workflow.add_edge("execute_tool", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()


# Compiled agent graph instance
agent_app = build_lineage_agent_graph()


def run_agent(session_id: str, query: str) -> ChatResponse:
    """Execute the LangGraph agent for a user query on a specific session."""
    initial_state: AgentState = {
        "messages": [],
        "user_query": query,
        "session_id": session_id,
        "metadata_context": {},
        "tool_results": {},
        "tools_used": [],
        "sources": [],
        "final_answer": None,
    }

    final_state = agent_app.invoke(initial_state)

    return ChatResponse(
        answer=final_state.get("final_answer") or "I could not generate an answer.",
        tools_used=final_state.get("tools_used", []),
        sources=final_state.get("sources", []),
    )
