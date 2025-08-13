from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import zipfile
import os
import shutil
from pathlib import Path
import json
from typing import Dict, List, Any
import aiofiles
import asyncio

# CREATE THE FASTAPI APP - This line is crucial!
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = Path("uploads")
EXTRACT_DIR = Path("datasets")
STATIC_DIR = Path("static")
TEMPLATES_DIR = Path("templates")
ALLOWED_EXTENSIONS = {'.zip'}

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
EXTRACT_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

def get_file_structure(path: Path) -> Dict[str, Any]:
    """Recursively get file structure of a directory"""
    structure = {
        "name": path.name,
        "type": "directory",
        "path": str(path),
        "children": []
    }
    
    try:
        for item in sorted(path.iterdir()):
            if item.is_dir():
                structure["children"].append(get_file_structure(item))
            else:
                structure["children"].append({
                    "name": item.name,
                    "type": "file",
                    "path": str(item),
                    "size": item.stat().st_size
                })
    except PermissionError:
        pass
    
    return structure

def find_dataset_root(extract_path: Path) -> Path:
    """Find the actual dataset root directory - IMPROVED VERSION"""
    
    print(f"🔍 Looking for dataset root in: {extract_path}")
    
    items = list(extract_path.iterdir())
    print(f"🔍 Found {len(items)} items in extract path: {[item.name for item in items]}")
    
    # If there's only one directory, check what's inside it
    if len(items) == 1 and items[0].is_dir():
        nested_path = items[0]
        nested_items = list(nested_path.iterdir())
        class_dirs = [item for item in nested_items if item.is_dir() and not item.name.startswith('.')]
        
        print(f"🔍 Nested path '{nested_path.name}' has {len(class_dirs)} directories")
        print(f"🔍 Sample directories: {[d.name for d in class_dirs[:5]]}")
        
        # If the nested directory has many class directories (like accordion, airplane, etc), use it
        if len(class_dirs) > 10:  # Caltech 101 should have ~102 classes
            print(f"✅ Using nested path as dataset root: {nested_path}")
            return nested_path
        else:
            print(f"⚠️ Not enough class directories found in nested path")
    
    # Count class directories in the original path
    original_class_dirs = [item for item in items if item.is_dir() and not item.name.startswith('.')]
    print(f"🔍 Original path has {len(original_class_dirs)} class directories")
    
    if len(original_class_dirs) > 10:
        print(f"✅ Using original path as dataset root: {extract_path}")
        return extract_path
    else:
        print(f"⚠️ Using original path by default: {extract_path}")
        return extract_path

def get_dataset_stats(path: Path) -> Dict[str, Any]:
    """Get statistics about the dataset - FIXED VERSION"""
    stats = {
        "total_folders": 0,
        "total_files": 0,
        "total_images": 0,
        "classes": [],
        "file_types": {},
        "dataset_name": path.name
    }
    
    print(f"📊 Analyzing dataset at: {path}")
    print(f"📊 Path exists: {path.exists()}")
    
    if not path.exists():
        print("❌ ERROR: Path does not exist!")
        return stats
    
    # Image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    
    try:
        items = list(path.iterdir())
        print(f"📊 Found {len(items)} items")
        
        # Show first few items for debugging
        for i, item in enumerate(items[:10]):
            item_type = "📁 DIR" if item.is_dir() else "📄 FILE"
            print(f"   {i+1:2d}. {item_type} {item.name}")
        
        if len(items) > 10:
            print(f"   ... and {len(items) - 10} more items")
        
        for item in items:
            if item.is_dir() and not item.name.startswith('.'):
                print(f"📂 Processing class directory: {item.name}")
                stats["total_folders"] += 1
                
                class_info = {
                    "name": item.name,
                    "count": 0,
                    "files": []
                }
                
                # Count files in class directory
                try:
                    class_files = list(item.iterdir())
                    for file in class_files:
                        if file.is_file() and not file.name.startswith('.'):
                            stats["total_files"] += 1
                            class_info["count"] += 1
                            class_info["files"].append(file.name)
                            
                            ext = file.suffix.lower()
                            stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1
                            
                            if ext in image_extensions:
                                stats["total_images"] += 1
                    
                    print(f"   ✅ {item.name}: {class_info['count']} files")
                    
                except Exception as e:
                    print(f"   ❌ Error processing {item.name}: {e}")
                    continue
                
                if class_info["count"] > 0:
                    stats["classes"].append(class_info)
            else:
                if item.is_file():
                    print(f"📄 Skipping file: {item.name}")
        
        stats["classes"].sort(key=lambda x: x["count"], reverse=True)
        
        print(f"✅ FINAL STATS:")
        print(f"   📁 Classes: {stats['total_folders']}")
        print(f"   🖼️  Images: {stats['total_images']}")
        print(f"   📄 Files: {stats['total_files']}")
        print(f"   📊 Valid classes with files: {len(stats['classes'])}")
        
        # Show top 5 classes
        if stats['classes']:
            print(f"   🏆 Top 5 classes:")
            for i, cls in enumerate(stats["classes"][:5]):
                print(f"      {i+1}. {cls['name']}: {cls['count']} images")
        
    except Exception as e:
        print(f"❌ Error in get_dataset_stats: {e}")
        import traceback
        traceback.print_exc()
    
    return stats
@app.get("/")
async def read_root():
    """API status"""
    return {
        "message": "Caltech 101 Dataset Explorer API",
        "status": "running",
        "endpoints": {
            "upload": "/api/upload",
            "datasets": "/api/datasets",
            "structure": "/api/dataset/{dataset_name}/structure",
            "class_details": "/api/dataset/{dataset_name}/class/{class_name}"
        }
    }

@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload and extract dataset zip file"""
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed")
    
    upload_path = UPLOAD_DIR / file.filename
    
    try:
        # Save file
        async with aiofiles.open(upload_path, 'wb') as f:
            while chunk := await file.read(8 * 1024 * 1024):
                await f.write(chunk)
        
        print(f"File saved: {upload_path}")
        
        # Extract
        dataset_name = Path(file.filename).stem
        extract_path = EXTRACT_DIR / dataset_name
        
        if extract_path.exists():
            shutil.rmtree(extract_path)
        
        with zipfile.ZipFile(upload_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        print(f"Extracted to: {extract_path}")
        
        # Find the actual dataset root (handles nested directories)
        actual_dataset_path = find_dataset_root(extract_path)
        print(f"Using dataset path: {actual_dataset_path}")
        
        # Get statistics from correct path
        file_structure = get_file_structure(actual_dataset_path)
        dataset_stats = get_dataset_stats(actual_dataset_path)
        
        # Clean up
        upload_path.unlink()
        
        return {
            "success": True,
            "message": "Dataset uploaded and extracted successfully",
            "dataset_name": dataset_name,
            "structure": file_structure,
            "stats": dataset_stats
        }
        
    except Exception as e:
        if upload_path.exists():
            upload_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/datasets")
async def list_datasets():
    """List all available datasets - FIXED"""
    datasets = []
    
    for dataset_dir in EXTRACT_DIR.iterdir():
        if dataset_dir.is_dir():
            print(f"🔍 Processing dataset directory: {dataset_dir.name}")
            
            # Use find_dataset_root to get correct path for stats
            actual_path = find_dataset_root(dataset_dir)
            stats = get_dataset_stats(actual_path)
            
            datasets.append({
                "name": dataset_dir.name,
                "path": str(dataset_dir),
                "stats": stats
            })
    
    return {"datasets": datasets}

@app.get("/api/dataset/{dataset_name}/structure")
async def get_dataset_structure(dataset_name: str):
    """Get the file structure of a specific dataset - FIXED"""
    base_path = EXTRACT_DIR / dataset_name
    
    if not base_path.exists():
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_name}' not found")
    
    print(f"🔍 Getting structure for dataset: {dataset_name}")
    print(f"🔍 Base path: {base_path}")
    
    # Find the actual dataset root (this is the key fix!)
    actual_path = find_dataset_root(base_path)
    print(f"🔍 Using actual path: {actual_path}")
    
    structure = get_file_structure(actual_path)
    stats = get_dataset_stats(actual_path)
    
    return {
        "structure": structure,
        "stats": stats
    }

@app.get("/api/dataset/{dataset_name}/class/{class_name}")
async def get_class_details(dataset_name: str, class_name: str):
    """Get details about a specific class in the dataset"""
    base_path = EXTRACT_DIR / dataset_name
    actual_path = find_dataset_root(base_path)
    class_path = actual_path / class_name
    
    if not class_path.exists():
        raise HTTPException(status_code=404, detail=f"Class '{class_name}' not found")
    
    files = []
    for file in class_path.iterdir():
        if file.is_file():
            files.append({
                "name": file.name,
                "size": file.stat().st_size,
                "path": str(file)
            })
    
    return {
        "class_name": class_name,
        "file_count": len(files),
        "files": files
    }