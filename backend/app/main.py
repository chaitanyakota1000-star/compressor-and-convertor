from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import upload, compress, download, auth, convert
import logging
import asyncio
import time
from pathlib import Path
from app.config import UPLOAD_DIR, COMPRESSED_DIR
from app.database import uploaded_files, compressed_files

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Universal File & Image Compressor API",
    description="Backend API for compression of images, PDFs, text, and other files with user auth.",
    version="1.1.0"
)

# Enable CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(compress.router, prefix="/api", tags=["Compression"])
app.include_router(download.router, prefix="/api", tags=["Download"])
app.include_router(convert.router, prefix="/api", tags=["Conversion"])

async def periodic_cleanup():
    """
    Asynchronous task that runs in the background and deletes temporary 
    uploaded and compressed files that are older than 15 minutes (900s).
    """
    logger.info("Starting periodic temporary file cleanup task...")
    while True:
        try:
            now = time.time()
            max_age_seconds = 15 * 60  # 15 minutes
            
            # 1. Clean uploads directory
            for file_path in UPLOAD_DIR.glob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    # Use last modification time or metadata size
                    if now - stat.st_mtime > max_age_seconds:
                        file_path.unlink()
                        logger.info(f"Cleanup: Deleted old uploaded file: {file_path.name}")
                        
                        # Remove metadata from uploaded_files database
                        fids_to_del = [fid for fid, meta in uploaded_files.items() if Path(meta["path"]) == file_path]
                        for fid in fids_to_del:
                            del uploaded_files[fid]
                            
            # 2. Clean compressed directory
            for file_path in COMPRESSED_DIR.glob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    if now - stat.st_mtime > max_age_seconds:
                        file_path.unlink()
                        logger.info(f"Cleanup: Deleted old compressed file: {file_path.name}")
                        
                        # Remove metadata from compressed_files database
                        dids_to_del = [did for did, meta in compressed_files.items() if Path(meta["path"]) == file_path]
                        for did in dids_to_del:
                            del compressed_files[did]
                            
        except Exception as e:
            logger.error(f"Error in periodic cleanup execution: {e}")
            
        # Run every 60 seconds
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    # Schedule the cleanup task to run in the background event loop
    asyncio.create_task(periodic_cleanup())

@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "Universal File & Image Compressor API",
        "auth": "active",
        "range_requests": "active"
    }
