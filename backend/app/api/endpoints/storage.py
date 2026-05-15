import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from loguru import logger

router = APIRouter()

# Use the metadata volume for persistence
UPLOAD_DIR = "/app/data/uploads"

# Ensure upload directory exists during startup
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Handles secure file uploads for QueryBridge CSV/Excel sources.
    Adheres to enterprise storage patterns by using the managed data volume.
    """
    # 1. Validation
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.csv', '.xlsx', '.xls']:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format {ext}. Please upload CSV or Excel files."
        )
    
    # 2. Secure Filename Generation
    file_id = str(uuid.uuid4())[:8]
    safe_filename = f"{file_id}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    # 3. Streamed Write
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Enterprise File Upload Successful: {safe_filename} [Path: {file_path}]")
        
        return {
            "success": True,
            "file_path": file_path,
            "filename": file.filename,
            "size": os.path.getsize(file_path)
        }
    except Exception as e:
        logger.error(f"File system write failure: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to persist uploaded file to storage volume.")

@router.delete("/{filename}")
async def delete_file(filename: str):
    """Cleanup uploaded files."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"success": True}
    raise HTTPException(status_code=404, detail="File not found")
