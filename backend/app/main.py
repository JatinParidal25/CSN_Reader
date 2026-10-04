import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes_agent import router as agent_router
from app.api.routes_metadata import router as metadata_router
from app.api.routes_upload import router as upload_router
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("datasphere_agent")

app = FastAPI(
    title=settings.app_name,
    description="Deterministic metadata extraction, lineage analysis, and LangGraph agent for SAP Datasphere CSN",
    version="1.0.0",
)

# Configure CORS
origins = [
    settings.frontend_url,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler to never leak raw internal stacktraces to client
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred while processing the request."},
    )

# Include API routes
app.include_router(upload_router)
app.include_router(metadata_router)
app.include_router(agent_router)


@app.get("/api/health", tags=["health"])
def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": "1.0.0",
        "llm_provider": settings.llm_provider,
        "fallback_mode": settings.development_fallback_mode,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
