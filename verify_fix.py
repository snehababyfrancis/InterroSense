import requests
import os
import time

try:
    # 1. Check if files exist
    fst_dir = r"d:\introproject\media\fst_data"
    if os.path.exists(fst_dir) and len(os.listdir(fst_dir)) > 0:
        print(f"Files exist in {fst_dir} (Initial state)")
    else:
        print(f"{fst_dir} does not exist or is empty. Please ensure data exists before verifying.")

    # 2. Trigger load_questions
    print("Triggering load_questions...")
    response = requests.post("http://127.0.0.1:8000/load_questions/", json={"scenario": "test", "accused_id": "123"})
    print(f"Status Code: {response.status_code}")
    
    # 3. Check if files are gone
    if os.path.exists(fst_dir):
        files = os.listdir(fst_dir)
        print(f"Files in {fst_dir} after request: {len(files)}")
        if len(files) == 0:
            print("SUCCESS: Directory cleared.")
        else:
             print("FAILURE: Directory not cleared.")
    else:
        print("SUCCESS: Directory removed.")

except Exception as e:
    print(f"Error: {e}")
