import os
import glob
import datetime
import json
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- CONFIGURATION ---
SERVICE_ACCOUNT_INFO = os.environ.get('GDRIVE_CREDENTIALS_JSON')
PARENT_FOLDER_ID = os.environ.get('GDRIVE_FOLDER_ID')

def authenticate():
    print("  [Drive Init] Loading credentials...")
    
    if not SERVICE_ACCOUNT_INFO:
        print("  [Error] GDRIVE_CREDENTIALS_JSON secret is missing.")
        return None
    if not PARENT_FOLDER_ID:
        print("  [Error] GDRIVE_FOLDER_ID secret is missing.")
        return None
    
    try:
        # Parse the JSON string
        info = json.loads(SERVICE_ACCOUNT_INFO)
        
        # DEBUG: Print who the robot thinks it is
        print(f"  [Debug] Authenticating as: {info.get('client_email', 'Unknown')}")
        
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=['https://www.googleapis.com/auth/drive']
        )
        service = build('drive', 'v3', credentials=creds)
        return service
    except json.JSONDecodeError:
        print("  [Error] The GDRIVE_CREDENTIALS_JSON secret is not valid JSON. Did you paste the whole file?")
        return None
    except Exception as e:
        print(f"  [Auth Error] {e}")
        return None

def verify_folder_access(service):
    """Checks if the robot can actually see the folder."""
    try:
        file = service.files().get(fileId=PARENT_FOLDER_ID, fields='name').execute()
        print(f"  [Success] Connected to folder: '{file.get('name')}'")
        return True
    except Exception as e:
        print(f"  [Access Error] Could not find folder. Check permissions! Error: {e}")
        print("  HINT: Did you share the folder with the 'client_email' listed above as 'Editor'?")
        return False

def create_weekly_folder(service, folder_name):
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [PARENT_FOLDER_ID]
    }
    file = service.files().create(body=file_metadata, fields='id').execute()
    return file.get('id')

def upload_files(service):
    # Upload only high-value reports to avoid clutter
    patterns = [
        "WEEKLY_SYNTHESIS.md",
        "EXECUTIVE_BRIEF.md",
        "CONNECT_THE_DOTS.md", # Added the new report
        "DEEP_DIVE_*.md"
    ]
    
    files_found = []
    for pattern in patterns:
        files_found.extend(glob.glob(pattern))
    
    if not files_found:
        print("  [Warning] No report files found to upload.")
        print("  (This is normal if the Synthesizer step failed or found no data).")
        return

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d Research Batch')
    
    try:
        batch_folder_id = create_weekly_folder(service, timestamp)
        print(f"  [Drive] Created sub-folder: {timestamp}")

        for file_path in files_found:
            file_name = os.path.basename(file_path)
            
            file_metadata = {
                'name': file_name,
                'parents': [batch_folder_id]
            }
            
            media = MediaFileUpload(file_path, mimetype='text/markdown')
            
            try:
                service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                print(f"  [Uploaded] {file_name}")
            except Exception as e:
                print(f"  [Upload Error] {file_name}: {e}")
                
    except Exception as e:
        print(f"  [Folder Error] Could not create sub-folder: {e}")

if __name__ == "__main__":
    service = authenticate()
    if service:
        if verify_folder_access(service):
            upload_files(service)
