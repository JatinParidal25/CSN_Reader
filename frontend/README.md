# Frontend: SAP Datasphere Metadata & Lineage Agent

Modern React + TypeScript + Vite web interface for visualizing SAP Datasphere metadata, relationships, lineage, and interacting with the LangGraph copilot.

## Tech Stack
- **React 19 + TypeScript**
- **Vite 6**
- **Lucide Icons**
- **Axios**
- **Modern Responsive Dark Mode CSS**

## Running Locally

```powershell
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

The frontend will run at `http://localhost:5173`.
To point to a custom backend URL, set the `VITE_API_URL` environment variable:
```powershell
$env:VITE_API_URL="http://localhost:8000"
npm run dev
```

## Features
- **CSN Upload**: Drag-and-drop or 1-click load of sample Datasphere CSN JSON files.
- **Metrics Dashboard**: Instant overview of entities, relationships, measures, and fields.
- **Object Catalog**: Searchable and filterable by modeling pattern (`ANALYTICAL_CUBE`, `ANALYTICAL_FACT`, `ANALYTICAL_DIMENSION`, `ENTITY`).
- **Object Details**: Detailed inspection of fields (keys, data types, measures, aggregations), associations, and hierarchies.
- **Visual Lineage Graph**: Upstream source dependencies ➔ Focus Object ➔ Downstream consumers.
- **Impact Analysis**: Immediate assessment of risk level (CRITICAL / HIGH / MEDIUM / LOW), direct dependents, and affected models.
- **AI Copilot**: Natural language interface powered by LangGraph, grounded by deterministic retrieval tools.
