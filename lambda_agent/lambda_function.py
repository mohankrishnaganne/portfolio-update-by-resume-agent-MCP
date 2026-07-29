import json
import os
import urllib.parse
from datetime import datetime

from Services.s3_service import download_from_s3
from Services.pdf_service import extract_text_from_pdf
from Services.ai_agent_service import generate_and_commit_portfolio
from Services.upload_logger import log_resume_upload

def lambda_handler(event, context):
    print("Received S3 Event: ", json.dumps(event))
    
    try:
        print("Welcome to My Portfolio Creator! 🚀")
        # 1. Parse bucket and filename from the S3 event trigger
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
        resume_filename = os.path.basename(key)
        
        # 2. Download the file to Lambda's writable /tmp directory
        download_path = f"/tmp/{resume_filename}"
        download_from_s3(bucket, key, download_path)
        
        # 3. Extract text from the downloaded PDF
        with open(download_path, 'rb') as file_obj:
            resume_text = extract_text_from_pdf(file_obj)
        
        # 4. Define AI Variables
        repo_name = "mcp-demo-repo"
        file_path = "portfolio.html"
        github_username = "mohankrishnaganne"
        upload_timestamp = datetime.now().isoformat()
        
        # 5. Trigger AI Generation and GitHub Commit
        print(f"[System] Triggering AI Agent for {resume_filename}...")
        generate_and_commit_portfolio(
            resume_text=resume_text, 
            repo_name=repo_name, 
            file_path=file_path,
            github_username=github_username,
            resume_filename=resume_filename,
            upload_timestamp=upload_timestamp,
            s3_key=key
        )
        
        # 6. Log the upload locally in the container
        log_resume_upload(resume_filename, upload_timestamp, key)
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Successfully processed {resume_filename} and committed to GitHub.')
        }
        
    except Exception as e:
        print(f"[Error] Lambda execution failed: {str(e)}")
        raise e