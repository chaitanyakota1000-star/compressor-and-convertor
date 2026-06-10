from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from pathlib import Path
import logging

from app.config import COMPRESSED_DIR, SUPPORTED_IMAGE_EXTENSIONS
from app.database import uploaded_files, compressed_files
from app.dependencies import get_current_user
from app.utils import (
    convert_images_to_pdf,
    convert_pdf_to_images,
    convert_pdf_to_docx,
    convert_docx_to_pdf,
    create_zip_archive
)

logger = logging.getLogger(__name__)
router = APIRouter()

class ConvertRequest(BaseModel):
    file_ids: List[str] = Field(..., min_items=1, description="List of uploaded file IDs to convert")
    conversion_type: str = Field(..., description="Conversion format (image_to_pdf, pdf_to_image, pdf_to_docx, docx_to_pdf)")
    target_img_format: str = Field("PNG", description="Target format for PDF-to-image conversion (PNG, JPEG)")

@router.post("/convert")
async def convert_files(request: ConvertRequest, current_user: dict = Depends(get_current_user)):
    # Validate file IDs
    valid_files = []
    for fid in request.file_ids:
        if fid not in uploaded_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid or expired file ID: {fid}"
            )
        valid_files.append((fid, uploaded_files[fid]))
        
    conv_type = request.conversion_type.lower().strip()
    allowed_types = {"image_to_pdf", "pdf_to_image", "pdf_to_docx", "docx_to_pdf"}
    if conv_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported conversion type: {conv_type}. Supported: {list(allowed_types)}"
        )
        
    download_id = str(uuid.uuid4())
    
    try:
        # 1. IMAGE TO PDF
        if conv_type == "image_to_pdf":
            image_paths = []
            for fid, meta in valid_files:
                filepath = Path(meta["path"])
                ext = filepath.suffix.lower()
                if ext not in SUPPORTED_IMAGE_EXTENSIONS:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"File {meta['filename']} is not a supported image format."
                    )
                image_paths.append(filepath)
                
            out_filename = "converted_images.pdf" if len(valid_files) > 1 else f"converted_{Path(valid_files[0][1]['filename']).stem}.pdf"
            out_path = COMPRESSED_DIR / f"{download_id}.pdf"
            
            convert_images_to_pdf(image_paths, out_path)
            
        # 2. PDF TO IMAGE
        elif conv_type == "pdf_to_image":
            if len(valid_files) > 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PDF page rendering only supports converting one PDF file at a time."
                )
            fid, meta = valid_files[0]
            filepath = Path(meta["path"])
            if filepath.suffix.lower() != ".pdf":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Please select a valid PDF file to render."
                )
                
            target_ext = "jpg" if request.target_img_format.upper() in ("JPEG", "JPG") else "png"
            page_images = convert_pdf_to_images(filepath, COMPRESSED_DIR, request.target_img_format)
            
            if len(page_images) == 1:
                # Single page, return image directly
                out_filename = f"{Path(meta['filename']).stem}_page1.{target_ext}"
                out_path = page_images[0]
                # Rename the generated file to match session ID to avoid collisions
                new_path = COMPRESSED_DIR / f"{download_id}.{target_ext}"
                out_path.rename(new_path)
                out_path = new_path
            else:
                # Multiple pages, package into a zip archive
                out_filename = f"{Path(meta['filename']).stem}_pages.zip"
                out_path = COMPRESSED_DIR / f"{download_id}.zip"
                
                # Zip the page files
                files_to_zip = [(p, p.name) for p in page_images]
                create_zip_archive(files_to_zip, out_path)
                
                # Delete temporary individual page files
                for p in page_images:
                    if p.exists():
                        p.unlink()
                        
        # 3. PDF TO WORD (.docx)
        elif conv_type == "pdf_to_docx":
            if len(valid_files) > 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PDF to Word conversion only supports converting one file at a time."
                )
            fid, meta = valid_files[0]
            filepath = Path(meta["path"])
            if filepath.suffix.lower() != ".pdf":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Please select a valid PDF document."
                )
                
            out_filename = f"{Path(meta['filename']).stem}.docx"
            out_path = COMPRESSED_DIR / f"{download_id}.docx"
            
            convert_pdf_to_docx(filepath, out_path)
            
        # 4. WORD TO PDF
        elif conv_type == "docx_to_pdf":
            if len(valid_files) > 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Word to PDF conversion only supports converting one file at a time."
                )
            fid, meta = valid_files[0]
            filepath = Path(meta["path"])
            if filepath.suffix.lower() != ".docx":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Please select a valid Word document (.docx)."
                )
                
            out_filename = f"{Path(meta['filename']).stem}.pdf"
            out_path = COMPRESSED_DIR / f"{download_id}.pdf"
            
            convert_docx_to_pdf(filepath, out_path)
            
        # Register compressed/converted file details
        file_size = out_path.stat().st_size
        compressed_files[download_id] = {
            "path": out_path,
            "filename": out_filename,
            "size": file_size
        }
        
        # Clean up raw uploads
        for fid in request.file_ids:
            try:
                meta = uploaded_files[fid]
                filepath = Path(meta["path"])
                if filepath.exists():
                    filepath.unlink()
                del uploaded_files[fid]
                logger.info(f"Cleanup: Deleted raw uploaded file: {filepath.name}")
            except Exception as e:
                logger.warning(f"Failed to delete source file during cleanup: {e}")
                
        logger.info(f"Conversion completed successfully: {out_filename} (ID: {download_id})")
        return {
            "download_id": download_id,
            "filename": out_filename,
            "size": file_size
        }
        
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversion failed: {str(e)}"
        )
