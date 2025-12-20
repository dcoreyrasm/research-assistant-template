import os
import dropbox
import datetime
import glob
from dropbox.exceptions import AuthError

# --- CONFIGURATION ---
DROPBOX_APP_KEY = os.environ.get('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = os.environ.get('DROPBOX_APP_SECRET')
DROPBOX_REFRESH_TOKEN = os.environ.get('DROPBOX_REFRESH_TOKEN')

def setup_dropbox():
    """Authenticates using the Refresh Token."""
    if not DROPBOX_REFRESH_TOKEN:
        print("Error: Missing Dropbox Refresh Token.")
        return None
    
    try:
        # Use Refresh Token to get a new Access Token
        dbx = dropbox.Dropbox(
            app_key=DROPBOX_APP_KEY,
            app_secret=DROPBOX_APP_SECRET,
            oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
        )
        
        # Test connection
        account = dbx.users_get_current_account()
        print(f"  [Success] Connected to Dropbox account: {account.name.display_name}")
        return dbx
        
    except AuthError as e:
        print(f"  [Error] Authentication failed: {e}")
        return None
    except Exception as e:
        print(f"  [Error] Connection error: {e}")
        return None

def upload_reports():
    dbx = setup_dropbox()
    if not dbx: return

    # create a timestamped folder
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    folder_path = f"/{timestamp} - Research Batch"
    
    # 1. Grab ALL markdown files AND HTML files
    files_to_upload = glob.glob("*.md") + glob.glob("*.html")
    
    # 2. Also grab the CSV data for backup
    if os.path.exists("literature_matrix.csv"):
        files_to_upload.append("literature_matrix.csv")

    if not files_to_upload:
        print("No reports found to upload.")
        return

    print(f"Uploading {len(files_to_upload)} files to Dropbox folder: {folder_path}")

    for local_file in files_to_upload:
        try:
            with open(local_file, "rb") as f:
                # Upload to specific batch folder
                dbx.files_upload(f.read(), f"{folder_path}/{local_file}")
                print(f"  [Uploaded] {local_file}")
                
                # OPTIONAL: Also update a "LATEST" folder so you always know where to look
                # This overwrites the file in /LATEST so it's always fresh
                with open(local_file, "rb") as f_latest:
                     dbx.files_upload(f_latest.read(), f"/LATEST_REPORTS/{local_file}", mode=dropbox.files.WriteMode.overwrite)

        except Exception as e:
            print(f"  [Upload Error] Failed to upload {local_file}: {e}")

if __name__ == "__main__":
    upload_reports()
