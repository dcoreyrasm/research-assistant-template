import dropbox
import os
import glob
import datetime
import sys

# --- CONFIGURATION ---
# We stick .strip() on the end to remove any accidental spaces from copy-pasting
# We also strip quotes and brackets just in case you copied the JSON format directly
APP_KEY = os.environ.get('DROPBOX_APP_KEY', '').strip().strip('"').strip("'")
APP_SECRET = os.environ.get('DROPBOX_APP_SECRET', '').strip().strip('"').strip("'")
REFRESH_TOKEN = os.environ.get('DROPBOX_REFRESH_TOKEN', '').strip().strip('"').strip("'").strip("{}")

def setup_dropbox():
    # Debug print length (safe) to verify secrets are loaded
    print(f"  [Debug] App Key Length: {len(APP_KEY)}")
    print(f"  [Debug] Secret Length: {len(APP_SECRET)}")
    print(f"  [Debug] Refresh Token Length: {len(REFRESH_TOKEN)}")

    if not REFRESH_TOKEN or not APP_KEY or not APP_SECRET:
        print("Error: Missing Dropbox Credentials in GitHub Secrets.")
        return None
    
    print(f"  [Dropbox Init] Connecting with App Key: {APP_KEY[:4]}... (hidden)")
    
    # Initialize with Refresh Token for persistent access
    try:
        dbx = dropbox.Dropbox(
            app_key=APP_KEY,
            app_secret=APP_SECRET,
            oauth2_refresh_token=REFRESH_TOKEN
        )
        
        # Test the connection immediately
        # This will fail fast if the token is wrong, giving us a clear error
        account = dbx.users_get_current_account()
        print(f"  [Success] Connected to Dropbox account: {account.name.display_name}")
        return dbx
    except dropbox.exceptions.AuthError as e:
        print(f"  [Auth Error] The Refresh Token is rejected.")
        print(f"  Details: {e}")
        print("  ACTION: Please regenerate the Dropbox Refresh Token and update GitHub Secrets.")
        return None
    except Exception as e:
        print(f"  [Connection Error] {e}")
        return None

def upload_files(dbx):
    patterns = [
        "WEEKLY_SYNTHESIS.md",
        "EXECUTIVE_BRIEF.md",
        "DEEP_DIVE_*.md"
    ]
    
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    dropbox_folder = f"/{today} - Research Batch"
    
    files_found = []
    for pattern in patterns:
        files_found.extend(glob.glob(pattern))
    
    if not files_found:
        print("No reports found to upload.")
        return

    print(f"Uploading {len(files_found)} files to Dropbox folder: {dropbox_folder}")

    for file_path in files_found:
        with open(file_path, "rb") as f:
            file_name = os.path.basename(file_path)
            dropbox_path = f"{dropbox_folder}/{file_name}"
            
            try:
                dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
                print(f"  [Uploaded] {file_name}")
            except Exception as e:
                print(f"  [Upload Failed] {file_name}: {e}")

if __name__ == "__main__":
    dbx = setup_dropbox()
    if dbx:
        upload_files(dbx)
