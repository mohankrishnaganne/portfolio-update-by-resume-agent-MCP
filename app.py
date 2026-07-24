from flask import Flask, request, render_template
from datetime import datetime

from Services.s3_service import upload_to_s3
from Services.pdf_service import extract_text_from_pdf
from Services.ai_agent_service import generate_and_commit_portfolio
from Services.upload_logger import log_resume_upload

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'resume' not in request.files:
        return "No file uploaded", 400
        
    file = request.files['resume']
    if file.filename == '' or not file.filename.endswith('.pdf'):
        return "Invalid file type. Please upload a PDF.", 400

    try:
        # 1. Extract Text FIRST (before AWS closes the file)
        print("[System] Extracting PDF text...")
        resume_text = extract_text_from_pdf(file)
        print("[System] PDF text extracted successfully.")

        # Reset the file pointer back to the beginning before the upload
        file.seek(0)

        # 2. AWS Upload SECOND
        print("[System] Uploading to S3...")
        s3_key = upload_to_s3(file, file.filename)
        print(f"[System] S3 Upload complete: {s3_key}")

        # 3. AI Generation & GitHub Commit
        print("[System] Triggering AI Agent...")
        
        # Define your variables here
        repo_name = "portfolio-update-by-resume-agent-MCP"
        file_path = "portfolio.html"
        github_username = "mohankrishnaganne"
        resume_filename = file.filename
        upload_timestamp = datetime.now().isoformat()
        
        # Run the agent
        generate_and_commit_portfolio(
            resume_text=resume_text, 
            repo_name=repo_name, 
            file_path=file_path,
            github_username=github_username,
            resume_filename=resume_filename,
            upload_timestamp=upload_timestamp,
            s3_key=s3_key
        )
        print("[System] AI processing complete!")
        
        # Log the upload for audit trail
        log_resume_upload(resume_filename, upload_timestamp, s3_key)
        
        # Manually construct the bulletproof GitHub URL
        safe_github_url = f"https://github.com/{github_username}/{repo_name}/blob/main/{file_path}"
        
        return f"""
            <div style="font-family: sans-serif; text-align: center; margin-top: 50px;">
                <h2 style="color: #28a745;">Success! 🎉</h2>
                <p>Your Data Engineering portfolio was generated and committed to GitHub.</p>
                <a href='{safe_github_url}' target='_blank' style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">View Live on GitHub</a>
            </div>
        """
        
    except Exception as e:
        print(f"[Error] Pipeline failed: {str(e)}")
        return f"An error occurred during processing: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)