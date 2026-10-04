# SAP Datasphere Metadata & Lineage Agent

A complete, production-quality full-stack AI application for ingesting SAP Datasphere Core Schema Notation (CSN) JSON files, constructing an in-memory normalized metadata graph, computing deterministic upstream/downstream lineage and change impact analysis, and providing an intelligent LangGraph-powered conversational agent.

---

## 🏛️ Architectural Principle

> **Critical Design Principle: Raw CSN ≠ LLM Context**
>
> 1. **Zero Hallucination Parsing**: Large, complex SAP Datasphere CSN files are **never** dumped into an LLM prompt.
> 2. **Deterministic Processing**: A robust Python parser extracts entities, analytical cubes, dimensions, facts, fields, measures, aggregations, associations, hierarchies, and queries into a normalized graph (`NetworkX`).
> 3. **Deterministic Lineage Engine**: All upstream dependencies, downstream consumers, and change impact severities are calculated mathematically using graph algorithms in pure Python.
> 4. **LangGraph Copilot**: LangGraph orchestrates tool execution. The LLM is used solely for natural-language understanding, tool selection, reasoning, and clear explanation of deterministic findings.
> 5. **Small Model Friendly (~2B params)**: Because tool outputs are compact and focused, even small or local models (e.g., Llama 3 8B, Gemma 2B, or OpenAI GPT-4o-mini) operate with high accuracy.
> 6. **Development Fallback Mode**: The system includes a deterministic fallback mode that works out-of-the-box even without an OpenAI API key.

---

## 🛠️ Technology Stack

- **Backend**:
  - **Python 3.11+ / 3.12**
  - **FastAPI**: Asynchronous high-performance REST API
  - **Uvicorn**: ASGI web server
  - **Pydantic v2**: Data validation and type-safe schemas
  - **python-multipart**: Safe streaming multipart file uploads
  - **NetworkX**: In-memory directed graph for lineage and impact traversal
- **AI & Agent**:
  - **LangGraph**: StateGraph agent workflow
  - **LangChain Core & LangChain OpenAI**: OpenAI-compatible LLM abstraction
- **Frontend**:
  - **React 19 + TypeScript**: Type-safe modern component architecture
  - **Vite 6**: Fast bundler and development server
  - **Lucide React**: Clean developer-focused iconography
  - **Axios**: HTTP API client
  - **Vanilla Modern CSS**: Dark mode theme with sleek glassmorphism and responsiveness

---

## 📁 Project Structure

```
datasphere-copilot/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI application entrypoint & CORS
│   │   ├── config.py                   # Environment settings & configuration
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes_upload.py        # CSN upload & sample loader endpoints
│   │   │   ├── routes_metadata.py      # Normalized metadata, objects, lineage, impact
│   │   │   └── routes_agent.py         # AI agent chat endpoint
│   │   │
│   │   ├── parser/
│   │   │   ├── __init__.py
│   │   │   ├── csn_parser.py           # Defensive CSN JSON parser
│   │   │   ├── metadata_extractor.py   # Extraction helpers (fields, measures, assocs)
│   │   │   └── relationship_builder.py # Deterministic relationship builder
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── metadata_models.py      # Pydantic models for CSN structures
│   │   │   ├── api_models.py           # API request & response schemas
│   │   │   └── agent_models.py         # Agent state & tool schemas
│   │   │
│   │   ├── graph/
│   │   │   ├── __init__.py
│   │   │   ├── metadata_graph.py       # In-memory NetworkX directed graph
│   │   │   └── lineage.py              # Upstream/downstream lineage & impact analysis
│   │   │
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── state.py                # AgentState definition
│   │   │   ├── tools.py                # Deterministic tools (get_objects, get_lineage, etc.)
│   │   │   ├── nodes.py                # Tool execution node & response synthesizer
│   │   │   └── graph.py                # LangGraph StateGraph workflow definition
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── session_store.py        # In-memory session manager
│   │       └── llm_service.py          # OpenAI-compatible LLM provider abstraction
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_parser.py              # CSN parsing & extraction tests
│   │   ├── test_lineage.py             # Deterministic lineage & impact tests
│   │   └── test_api.py                 # FastAPI integration & chat tests
│   │
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.tsx          # Drag & drop upload + sample CSN loader
│   │   │   ├── Dashboard.tsx           # Metrics overview cards
│   │   │   ├── ObjectList.tsx          # Object sidebar with search & pattern tags
│   │   │   ├── ObjectDetails.tsx       # Fields, measures, associations, hierarchies
│   │   │   ├── LineageView.tsx         # Visual lineage graph & impact analysis
│   │   │   ├── ChatPanel.tsx           # Copilot conversational interface
│   │   │   ├── MessageBubble.tsx       # Rendered markdown bubbles with tools badge
│   │   │   └── LoadingIndicator.tsx    # Animated pulse & loader
│   │   │
│   │   ├── services/
│   │   │   └── api.ts                  # Axios API service
│   │   ├── types/
│   │   │   └── metadata.ts             # TypeScript interfaces
│   │   ├── App.tsx                     # Main layout & tab routing
│   │   ├── main.tsx                    # React DOM entrypoint
│   │   └── index.css                   # Theme tokens & styling
│   │
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md
│
├── sample_data/
│   └── sample_csn.json                 # Synthetic SAP Datasphere CSN sample
├── Current_Month_OI_Analytic_Model (1).json  # Full production Datasphere CSN (1.2 MB)
├── README.md
└── .gitignore
```

---

## 🔍 How It Works

### 1. CSN Parsing (`backend/app/parser/`)
- Ingests standard SAP Datasphere CSN / JSON containing:
  - `definitions`: entities, queries, views, contexts, structured types.
  - `businessLayerDefinitions`: Analytic Models with `factSources`, `dimensionSources`, `measures`, and `attributes`.
  - Annotation unwrapping: safely handles SAP CSN conventions such as `{"#": "ANALYTICAL_CUBE"}` or `{"=": "_FKDAT"}`.
  - Defensive extraction: missing optional fields never crash the system (`safe_get`, default fallbacks).
  - Extraction of leveled hierarchies (`@Hierarchy.leveled`) and navigation attributes (`@Analytics.navigationAttributeRef`).

### 2. Normalized Graph (`backend/app/graph/metadata_graph.py`)
- Nodes represent Datasphere objects (labeled with their modeling patterns: `ANALYTICAL_CUBE`, `ANALYTICAL_FACT`, `ANALYTICAL_DIMENSION`, `ENTITY`).
- Directed edges represent relationships: `SOURCE`, `FACT_SOURCE`, `DIMENSION_SOURCE`, `ASSOCIATION`, and `FOREIGN_KEY`.
- Traversal supports both upstream ancestor lookups and downstream dependent lookups.

### 3. Deterministic Lineage Engine (`backend/app/graph/lineage.py`)
- **`get_object_lineage(object_name)`**:
  - Returns direct and transitive upstream sources.
  - Returns direct and transitive downstream consumers.
  - Generates a localized visual subgraph of nodes and edges.
- **`get_impact_analysis(object_name)`**:
  - Deterministically evaluates direct dependents, downstream dependents, and upstream prerequisites.
  - Computes a risk rating: `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW`.
- **`get_field_lineage(object_name, field_name)`**:
  - Traces field origin across query projections (`query.SELECT.columns`), foreign key associations, and navigation attributes.
  - Returns clear explanation if field-level information is insufficient without hallucinating.

### 4. LangGraph Agent (`backend/app/agent/`)
- A clean compiled `StateGraph`:
  ```
  START ──> execute_tool ──> generate_response ──> END
  ```
- **Tools**:
  - `get_objects(session_id)`: Lists available Datasphere models.
  - `get_object_metadata(session_id, object_name)`: Returns complete object specification.
  - `get_lineage(session_id, object_name)`: Returns deterministic upstream/downstream tree.
  - `get_impact_analysis(session_id, object_name)`: Returns change impact assessment.
  - `get_field_metadata(session_id, object_name, field_name)`: Returns data type, measure flags, and aggregations.
  - `get_field_lineage(session_id, object_name, field_name)`: Returns field trace.
- **Hallucination Control**:
  - The agent system prompt mandates that the deterministic graph is the single source of truth.
  - The LLM synthesizes responses based strictly on tool outputs.
  - If information is missing, the agent explicitly responds that it is not available in the parsed CSN.

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.11+ / 3.12**
- **Node.js 18+ / 20+ / 22+**
- (Optional) **OpenAI API Key** (or any OpenAI-compatible server like Ollama, LMStudio, vLLM).

---

### Backend Setup (Windows PowerShell)

```powershell
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment variables (optional)
Copy-Item .env.example .env
# Edit .env with your OPENAI_API_KEY if desired (works out-of-the-box in fallback mode without it)

# 6. Start backend development server
uvicorn app.main:app --reload --port 8000
```

### Backend Setup (Linux / macOS)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

---

### Frontend Setup

```powershell
# Open a new terminal in the project root
cd frontend

# Install npm packages
npm install

# Start Vite dev server
npm run dev
```

Open your browser at **`http://localhost:5173`**.

---

## 🧪 Running Unit Tests

All unit tests run without requiring external network access or an active paid LLM key.

```powershell
# From the project root
$env:PYTHONPATH='backend'
.\backend\venv\Scripts\pytest.exe backend\tests -v
```

**Results:**
- `test_parser.py`: CSN loading, object extraction, measure extraction, association extraction, relationship creation, defensive handling.
- `test_lineage.py`: Object lineage, impact analysis, resolved field lineage, unknown field fallback, chain logic.
- `test_api.py`: Upload API, sample loader, metadata endpoint, lineage endpoint, impact endpoint, and chat copilot.
- **17 passed in the verified local run.**

---

## 🌐 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/upload` | Upload a CSN `.json` file and create an active session |
| `POST` | `/api/load-sample` | Quick-load bundled sample CSN (`?sample_type=sample` or `full`) |
| `GET` | `/api/metadata/{session_id}` | Return complete normalized metadata |
| `GET` | `/api/objects/{session_id}` | List all parsed objects |
| `GET` | `/api/object/{session_id}/{object_name}` | Get metadata for a specific object |
| `GET` | `/api/lineage/{session_id}/{object_name}` | Get deterministic upstream and downstream lineage |
| `GET` | `/api/impact/{session_id}/{object_name}` | Get change impact analysis for an object |
| `GET` | `/api/field-lineage/{session_id}/{object_name}/{field_name}` | Get field origin trace |
| `POST` | `/api/chat` | Send question to LangGraph copilot |
| `GET` | `/api/health` | Health check endpoint |

---

## 💬 Example Questions for the Agent

1. **"Show me all objects"**
   - Agent calls `get_objects` and displays a structured list with modeling patterns and measure counts.
2. **"Explain Current_Month_OI_Analytic_Model"**
   - Agent calls `get_object_metadata` and explains its modeling pattern (`ANALYTICAL_CUBE`), upstream sources, measures (`NETWR`), fields, and associations.
3. **"What is the lineage of Current_Month_OI_Analytic_Model?"**
   - Agent calls `get_lineage` and explains the upstream dependency path:
     `Current_Month_OI_Analytic_Model ➔ Current_Month_OI_Heirarchy ➔ Current_Month_Outgoing_Invoices ➔ VBRP & VBRK_1`.
4. **"What is NETWR?"**
   - Agent calls `get_field_metadata` and reports that `NETWR` is a measure with `SUM` default aggregation.
5. **"What happens if Time_table_heirarchy changes?"**
   - Agent calls `get_impact_analysis` and explains that `Current_Month_OI_Analytic_Model` and `Current_Month_OI_Heirarchy` are affected with `HIGH` risk severity.
6. **"What is the lineage of XYZ_NON_EXISTENT?"**
   - Agent calls `get_lineage` and explicitly responds that the entity does not exist in the parsed CSN metadata without inventing facts.

---

## 🔒 Security & Performance Considerations

- **Secure Execution**: Uploaded CSN files are treated as untrusted JSON data. No arbitrary code execution or deserialization exploits.
- **Upload Size Limits**: Configurable upload threshold (default 50 MB) prevents memory exhaustion.
- **Single-Pass Parsing**: The CSN is parsed once during upload and stored in an in-memory session. Chat and lineage operations query the pre-computed graph in sub-millisecond time.
- **Credential Protection**: API keys and environment variables are never returned in client responses.

---

## 🔮 Future-Ready Architecture

The modular separation enables seamless expansion to:
- Direct SAP Datasphere REST API connectivity
- Persistent database storage (PostgreSQL / Redis)
- Advanced SQL generation from analytical model queries
- Visual graph canvas enhancements using React Flow
- Multi-agent collaboration with specialized SAP SAC (Analytics Cloud) integration
