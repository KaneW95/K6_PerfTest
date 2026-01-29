from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import uuid
from typing import Dict

router = APIRouter()

# Define backend/data path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/data", tags=["Upload"])
async def upload_data_file(file: UploadFile = File(...)) -> Dict[str, str]:
    """Upload a data file (CSV) for data-driven testing."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing")
        
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # Generate safe filename to avoid collisions and directory traversal
    safe_filename = os.path.basename(file.filename)
    unique_filename = f"{uuid.uuid4().hex[:8]}_{safe_filename}"
    filepath = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
    # Return absolute path or relative path? 
    # Frontend/Backend interactions usually prefer absolute path for execution, 
    # but we should be careful. 
    # K6 Generator needs absolute path to read it.
    return {"filename": unique_filename, "path": filepath}

from fastapi.responses import StreamingResponse
import io

@router.get("/template/csv", tags=["Upload"])
async def download_csv_template():
    """Download a sample CSV template."""
    csv_content = "user_id,username,email\n1001,test_user,test@example.com"
    
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=template.csv"}
    )
