import json
import os
from datetime import datetime

# UPDATED: Lambda only allows writing to the /tmp directory
UPLOADS_LOG_FILE = "/tmp/resume_uploads_log.json"

def log_resume_upload(resume_filename: str, upload_timestamp: str, s3_key: str, github_commit_sha: str = None) -> None:
    uploads = []
    if os.path.exists(UPLOADS_LOG_FILE):
        try:
            with open(UPLOADS_LOG_FILE, 'r') as f:
                uploads = json.load(f)
        except (json.JSONDecodeError, IOError):
            uploads = []
    
    new_entry = {
        "resume_filename": resume_filename,
        "upload_timestamp": upload_timestamp,
        "s3_key": s3_key,
        "github_commit_sha": github_commit_sha,
        "logged_at": datetime.now().isoformat()
    }
    uploads.append(new_entry)
    
    with open(UPLOADS_LOG_FILE, 'w') as f:
        json.dump(uploads, f, indent=2)
    
    print(f"[System] Logged resume upload: {resume_filename}")

def get_uploads_history() -> list:
    if not os.path.exists(UPLOADS_LOG_FILE):
        return []
    try:
        with open(UPLOADS_LOG_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def get_latest_upload() -> dict:
    history = get_uploads_history()
    return history[-1] if history else None