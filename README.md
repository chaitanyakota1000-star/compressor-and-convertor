# ShrinkIO - Universal File & Image Compressor

ShrinkIO is a modern, premium full-stack web application designed for fast, secure, and intuitive file compression. It supports single-file image optimization, single-file document zipping, and bulk compression of multiple mixed files.

## Key Features

1. **Premium Responsive UI**: Built with a sleek dark theme featuring glassmorphism cards, glowing elements, and responsive designs.
2. **Interactive Drag-and-Drop**: Easy file uploading by dropping files in the zone or browsing local directories.
3. **Smart Image Optimization (Pillow)**:
   - Dynamic quality slider (1-100%) appears when at least one image file is added.
   - Adjusts JPEG/WebP quality and applies adaptive PNG color quantization to reduce size significantly while preserving visual quality.
4. **Universal Package Compression**:
   - Compresses PDF, TXT, CSV, and other data files by packaging them into compressed archives.
   - Supports `.zip` and `.tar.gz` archive formats.
5. **Bulk Compression**: Automatically bundles multiple files of any type into a single archive (applying image optimization to any images inside the bundle before packaging).
6. **Robust Stream Handling**: Chunked upload streaming and file response streaming keep server RAM footprint lightweight and stable even for large files (up to 500MB).
7. **Automated Server Cleanups**: Source uploads are deleted immediately after compression, and compressed archives are deleted automatically after download to save server space.

---

## Directory Structure

```
universal-compressor/
├── backend/
│   ├── app/
│   │   ├── routes/          # FastAPI routers (upload, compress, download)
│   │   ├── config.py        # Folder configuration and size limits
│   │   ├── database.py      # In-memory dictionary tracking file metadata
│   │   ├── utils.py         # Pillow image processing and archive generation
│   │   └── main.py          # FastAPI application bootstrapper
│   ├── venv/                # Local Python virtual environment
│   ├── requirements.txt     # Python backend dependencies
│   ├── run.py               # Backend dev server launcher
│   └── test_compress.py     # Integration test suite using TestClient
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # React state, Axios upload progress, styling
│   │   ├── index.css        # Tailwind CSS import and glassmorphism styling
│   │   └── main.jsx         # React application entry point
│   ├── index.html           # HTML container with Outfit font
│   ├── package.json         # Node dependencies
│   └── vite.config.js       # Vite configuration with proxy settings
├── README.md                # This documentation
└── start.bat                # Windows concurrent startup script
```

---

## Getting Started

### Prerequisites
- **Python 3.12+**
- **Node.js v20+** (The project runs using the preconfigured Node directory automatically on the system)

### Run the Application
Simply double-click the **`start.bat`** file in the root folder, or run it from command prompt:
```powershell
.\start.bat
```
This script will:
1. Boot the FastAPI backend server on `http://127.0.0.1:8000`.
2. Boot the React Vite dev server on `http://localhost:5173`.
3. Open two separate command prompt windows displaying live service logs.

---

## Verification & Testing

To run the automated API integration tests:
1. Open a terminal inside the `/backend` directory.
2. Run the test script using the virtual environment's Python:
   ```powershell
   venv\Scripts\python.exe test_compress.py
   ```
   This will execute the test suite via `pytest` and output the results.
