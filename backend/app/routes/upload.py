from fastapi import APIRouter, UploadFile, File, HTTPException, status
import uuid
from pathlib import Path
from app.config import UPLOAD_DIR, MAX_FILE_SIZE
from app.database import uploaded_files
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Create unique ID for the file
    file_id = str(uuid.uuid4())
    
    original_filename = file.filename or "unnamed_file"
    extension = Path(original_filename).suffix
    
    # Save path in uploads directory
    temp_filename = f"{file_id}{extension}"
    file_path = UPLOAD_DIR / temp_filename
    
    # Write chunked files to protect memory usage
    total_bytes = 0
    try:
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)}MB."
                    )
                buffer.write(chunk)
    except HTTPException:
        if file_path.exists():
            file_path.unlink()
        raise
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        logger.error(f"Error saving uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )
        
    # Store metadata
    uploaded_files[file_id] = {
        "path": file_path,
        "filename": original_filename,
        "size": total_bytes
    }
    
    logger.info(f"File uploaded successfully: {original_filename} (ID: {file_id})")
    
    return {
        "file_id": file_id,
        "filename": original_filename,
        "size": total_bytes
    }
