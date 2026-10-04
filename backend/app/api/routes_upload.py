import json
import os
from typing import Optional
from fastapi import APIRouter, File, HTTPException, UploadFile
from app.config import settings
from app.models.api_models import UploadResponse
from app.parser.csn_parser import CSNParser
from app.services.session_store import session_store

router = APIRouter(prefix="/api", tags=["upload"])
parser = CSNParser()


@router.post("/upload", response_model=UploadResponse)
async def upload_csn_file(file: UploadFile = File(...)):
    """Upload and parse a SAP Datasphere CSN JSON file."""
    if not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON/CSN files (.json) are supported.")

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # Check file size limit
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum allowed size of {settings.max_upload_size_mb} MB.",
            )

        # Parse CSN deterministically
        parsed_csn = parser.parse(content, filename=file.filename)

        # Store in session memory
        session_data = session_store.create_session(parsed_csn)

        return UploadResponse(
            success=True,
            session_id=session_data.session_id,
            filename=file.filename,
            object_count=parsed_csn.object_count,
            relationship_count=parsed_csn.relationship_count,
            field_count=parsed_csn.field_count,
            measure_count=parsed_csn.measure_count,
            message="CSN file parsed and metadata graph generated successfully.",
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file format: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"CSN validation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected parsing error: {str(e)}")


@router.post("/load-sample", response_model=UploadResponse)
async def load_sample_csn(sample_type: Optional[str] = "sample"):
    """Convenience endpoint to load the bundled sample CSN or original sample CSN."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    if sample_type == "full":
        candidates = [
            os.path.join(base_dir, "Current_Month_OI_Analytic_Model (1).json"),
            os.path.join(os.getcwd(), "Current_Month_OI_Analytic_Model (1).json"),
            os.path.join(os.getcwd(), "..", "Current_Month_OI_Analytic_Model (1).json"),
            "Current_Month_OI_Analytic_Model (1).json",
            "../Current_Month_OI_Analytic_Model (1).json",
        ]
    else:
        candidates = [
            os.path.join(base_dir, "sample_data", "sample_csn.json"),
            os.path.join(os.getcwd(), "sample_data", "sample_csn.json"),
            os.path.join(os.getcwd(), "..", "sample_data", "sample_csn.json"),
            "sample_data/sample_csn.json",
            "../sample_data/sample_csn.json",
        ]

    sample_path = next((p for p in candidates if os.path.exists(p)), None)
    if not sample_path:
        raise HTTPException(status_code=404, detail="Sample CSN file not found on server.")

    try:
        with open(sample_path, "r", encoding="utf-8") as f:
            content = f.read()

        filename = os.path.basename(sample_path)
        parsed_csn = parser.parse(content, filename=filename)
        session_data = session_store.create_session(parsed_csn)

        return UploadResponse(
            success=True,
            session_id=session_data.session_id,
            filename=filename,
            object_count=parsed_csn.object_count,
            relationship_count=parsed_csn.relationship_count,
            field_count=parsed_csn.field_count,
            measure_count=parsed_csn.measure_count,
            message=f"Sample '{filename}' loaded successfully.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading sample: {str(e)}")
