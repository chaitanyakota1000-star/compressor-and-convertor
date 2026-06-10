from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from pathlib import Path
import logging

from app.config import COMPRESSED_DIR, SUPPORTED_IMAGE_EXTENSIONS, SUPPORTED_ARCHIVE_FORMATS
from app.database import uploaded_files, compressed_files
from app.dependencies import get_current_user
from app.utils import compress_image, compress_image_to_target_size, create_zip_archive, create_tar_archive

logger = logging.getLogger(__name__)
router = APIRouter()

class CompressRequest(BaseModel):
    file_ids: List[str] = Field(..., min_items=1, description="List of uploaded file IDs to compress")
    quality: int = Field(80, ge=1, le=100, description="Quality compression ratio (1-100) for images")
    archive_format: str = Field("zip", description="Archive format ('zip' or 'tar.gz') for bulk compression")
    
    # New options for target size range optimization and format conversion
    optimize_size: bool = Field(False, description="Enable dynamic size optimization search")
    target_min_size: int = Field(0, description="Minimum target size in bytes")
    target_max_size: int = Field(0, description="Maximum target size in bytes")
    target_format: Optional[str] = Field(None, description="Image format conversion target (JPEG, PNG, WEBP)")

@router.post("/compress")
async def compress_files(request: CompressRequest, current_user: dict = Depends(get_current_user)):
    # Validate file IDs
    valid_files = []
    for fid in request.file_ids:
        if fid not in uploaded_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid or expired file ID: {fid}"
            )
        valid_files.append((fid, uploaded_files[fid]))
        
    # Validate archive format
    archive_fmt = request.archive_format.lower()
    if archive_fmt not in SUPPORTED_ARCHIVE_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported archive format: {archive_fmt}. Supported: {list(SUPPORTED_ARCHIVE_FORMATS)}"
        )
        
    # Parse format conversion target
    target_fmt = None
    if request.target_format:
        target_fmt = request.target_format.upper().strip()
        if target_fmt not in ("JPEG", "JPG", "PNG", "WEBP"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported target format: {target_fmt}. Supported: JPEG, PNG, WEBP."
            )
        if target_fmt == "JPG":
            target_fmt = "JPEG"

    download_id = str(uuid.uuid4())
    
    try:
        # Case 1: Single file upload
        if len(valid_files) == 1:
            fid, meta = valid_files[0]
            filepath = Path(meta["path"])
            orig_filename = meta["filename"]
            ext = filepath.suffix.lower()
            
            # Check if it's an image
            if ext in SUPPORTED_IMAGE_EXTENSIONS:
                # Determine output extension
                out_ext = f".{target_fmt.lower()}" if target_fmt else ext
                if out_ext == ".jpeg":
                    out_ext = ".jpg"
                    
                out_filename = f"compressed_{Path(orig_filename).stem}{out_ext}"
                out_path = COMPRESSED_DIR / f"{download_id}{out_ext}"
                
                # Apply size optimization or standard compression
                if request.optimize_size and request.target_max_size > 0:
                    compress_image_to_target_size(
                        filepath, out_path, 
                        request.target_min_size, 
                        request.target_max_size, 
                        target_fmt
                    )
                else:
                    compress_image(filepath, out_path, request.quality, target_fmt)
            else:
                # Non-image files: package in archive format
                if archive_fmt == "zip":
                    out_filename = f"{Path(orig_filename).stem}.zip"
                    out_path = COMPRESSED_DIR / f"{download_id}.zip"
                    create_zip_archive([(filepath, orig_filename)], out_path)
                else:  # tar.gz
                    out_filename = f"{Path(orig_filename).stem}.tar.gz"
                    out_path = COMPRESSED_DIR / f"{download_id}.tar.gz"
                    create_tar_archive([(filepath, orig_filename)], out_path)
        
        # Case 2: Multiple files upload (Bulk Compression)
        else:
            files_to_archive = []
            temp_compressed_files = []
            
            for fid, meta in valid_files:
                filepath = Path(meta["path"])
                orig_filename = meta["filename"]
                ext = filepath.suffix.lower()
                
                if ext in SUPPORTED_IMAGE_EXTENSIONS:
                    out_ext = f".{target_fmt.lower()}" if target_fmt else ext
                    if out_ext == ".jpeg":
                        out_ext = ".jpg"
                        
                    temp_img_id = str(uuid.uuid4())
                    temp_img_path = COMPRESSED_DIR / f"temp_{temp_img_id}{out_ext}"
                    
                    # Apply size optimization or standard compression
                    if request.optimize_size and request.target_max_size > 0:
                        compress_image_to_target_size(
                            filepath, temp_img_path, 
                            request.target_min_size, 
                            request.target_max_size, 
                            target_fmt
                        )
                    else:
                        compress_image(filepath, temp_img_path, request.quality, target_fmt)
                    
                    # Store temporary reference to delete after packing
                    files_to_archive.append((temp_img_path, f"{Path(orig_filename).stem}{out_ext}"))
                    temp_compressed_files.append(temp_img_path)
                else:
                    files_to_archive.append((filepath, orig_filename))
            
            # Build final archive
            if archive_fmt == "zip":
                out_filename = f"compressed_archive_{download_id[:8]}.zip"
                out_path = COMPRESSED_DIR / f"{download_id}.zip"
                create_zip_archive(files_to_archive, out_path)
            else:
                out_filename = f"compressed_archive_{download_id[:8]}.tar.gz"
                out_path = COMPRESSED_DIR / f"{download_id}.tar.gz"
                create_tar_archive(files_to_archive, out_path)
                
            # Clean up temporary compressed files
            for temp_f in temp_compressed_files:
                try:
                    if temp_f.exists():
                        temp_f.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temp compressed image {temp_f}: {e}")
                    
        # Register compressed file metadata
        file_size = out_path.stat().st_size
        compressed_files[download_id] = {
            "path": out_path,
            "filename": out_filename,
            "size": file_size
        }
        
        # Clean up original uploaded files from disk and database
        for fid in request.file_ids:
            try:
                meta = uploaded_files[fid]
                filepath = Path(meta["path"])
                if filepath.exists():
                    filepath.unlink()
                del uploaded_files[fid]
                logger.info(f"Cleaned up uploaded source file: {filepath.name}")
            except Exception as e:
                logger.warning(f"Failed to delete uploaded source file {fid}: {e}")

        logger.info(f"Compression completed: {out_filename} (ID: {download_id})")
        
        return {
            "download_id": download_id,
            "filename": out_filename,
            "size": file_size
        }
        
    except Exception as e:
        logger.error(f"Compression error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compression failed: {str(e)}"
        )
