from fastapi import APIRouter, HTTPException, status, Header
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
import re
from app.database import compressed_files
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/download/{download_id}")
async def download_file(download_id: str, range: str = Header(None)):
    if download_id not in compressed_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download session not found or link expired."
        )
        
    meta = compressed_files[download_id]
    file_path = Path(meta["path"])
    filename = meta["filename"]
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compressed file is missing or has been cleaned up."
        )
        
    file_size = file_path.stat().st_size
    
    # Handle HTTP Range Request (206 Partial Content)
    if range:
        # Range header format: "bytes=start-end"
        range_match = re.match(r"bytes=(\d+)-(\d*)", range)
        if range_match:
            start = int(range_match.group(1))
            end_str = range_match.group(2)
            end = int(end_str) if end_str else file_size - 1
            
            # Bounds check
            if start >= file_size or end >= file_size or start > end:
                raise HTTPException(
                    status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                    headers={"Content-Range": f"bytes */{file_size}"}
                )
                
            chunk_size = end - start + 1
            
            # Generator to read byte range from file
            def range_generator(path: Path, start_byte: int, length: int):
                with open(path, "rb") as f:
                    f.seek(start_byte)
                    bytes_remaining = length
                    while bytes_remaining > 0:
                        chunk_to_read = min(1024 * 1024, bytes_remaining)  # 1MB chunk max
                        data = f.read(chunk_to_read)
                        if not data:
                            break
                        bytes_remaining -= len(data)
                        yield data
                        
            logger.info(f"Serving range request: bytes {start}-{end}/{file_size} for {filename}")
            
            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_size),
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
            
            return StreamingResponse(
                range_generator(file_path, start, chunk_size),
                status_code=status.HTTP_206_PARTIAL_CONTENT,
                headers=headers,
                media_type="application/octet-stream"
            )
            
    # Standard full-file download response (200 OK)
    logger.info(f"Serving standard full-file request for {filename}")
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream",
        headers={"Accept-Ranges": "bytes"}
    )
