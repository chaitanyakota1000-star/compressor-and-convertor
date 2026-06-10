import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Temporary upload and compression directories inside the workspace
UPLOAD_DIR = BASE_DIR / "temp_uploads"
COMPRESSED_DIR = BASE_DIR / "temp_compressed"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
COMPRESSED_DIR.mkdir(parents=True, exist_ok=True)

# Max file size limit (500 MB)
MAX_FILE_SIZE = 500 * 1024 * 1024  

# Allowed image extensions
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

# Allowed archive formats
SUPPORTED_ARCHIVE_FORMATS = {"zip", "tar.gz"}

# JWT Authentication Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "antigravity_core_ultra_secret_key_99")
JWT_ALGORITHM = "HS256"

