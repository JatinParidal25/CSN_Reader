# Backend: SAP Datasphere Metadata & Lineage Agent

Deterministic CSN parsing, in-memory metadata graph traversal, lineage analysis, and LangGraph-powered conversational agent.

## Core Architectural Principle
The raw CSN is **never** sent to the LLM. Instead:
1. Python deterministically parses CSN JSON into a normalized metadata graph.
2. NetworkX directed graph powers upstream and downstream lineage and impact analysis.
3. LangGraph agent invokes deterministic tools to retrieve verified metadata.
4. LLM (or deterministic fallback) synthesizes explanations and natural language answers without hallucinations.

## Setup Instructions (Windows PowerShell)

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --port 8000
```

## Linux / macOS
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Running Unit Tests
```powershell
pytest tests -v
```

## Key API Endpoints
- `POST /api/upload`: Upload and parse CSN JSON.
- `POST /api/load-sample`: Load bundled synthetic or full sample CSN.
- `GET /api/metadata/{session_id}`: Retrieve parsed metadata for session.
- `GET /api/objects/{session_id}`: List all parsed objects.
- `GET /api/object/{session_id}/{object_name}`: Detailed object metadata.
- `GET /api/lineage/{session_id}/{object_name}`: Upstream and downstream lineage graph.
- `GET /api/impact/{session_id}/{object_name}`: Impact analysis.
- `GET /api/field-lineage/{session_id}/{object_name}/{field_name}`: Field-level lineage tracing.
- `POST /api/chat`: LangGraph conversational agent query.
- `GET /api/health`: Health status.
