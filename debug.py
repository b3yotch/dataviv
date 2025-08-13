import requests
import json

def debug_dataset_processing():
    print("=== DEBUGGING DATASET PROCESSING ===")
    
    # 1. Check API status
    try:
        response = requests.get("http://localhost:8000")
        print(f"✅ FastAPI Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ FastAPI Error: {e}")
        return
    
    # 2. Check datasets list
    try:
        response = requests.get("http://localhost:8000/api/datasets")
        datasets = response.json()
        print(f"📊 Available Datasets: {len(datasets.get('datasets', []))}")
        
        for dataset in datasets.get('datasets', []):
            print(f"   Dataset: {dataset.get('name')}")
            print(f"   Classes: {dataset.get('stats', {}).get('total_folders', 0)}")
            print(f"   Images: {dataset.get('stats', {}).get('total_images', 0)}")
    except Exception as e:
        print(f"❌ Datasets API Error: {e}")
    
    # 3. Check specific dataset structure
    try:
        response = requests.get("http://localhost:8000/api/dataset/caltech101/structure")
        structure = response.json()
        
        print(f"\n📁 Dataset Structure Response:")
        print(json.dumps(structure, indent=2)[:500] + "...")
        
    except Exception as e:
        print(f"❌ Structure API Error: {e}")

if __name__ == "__main__":
    debug_dataset_processing()