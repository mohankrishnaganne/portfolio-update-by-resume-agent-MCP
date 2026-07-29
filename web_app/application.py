import os
from flask import Flask, request, render_template
from s3_service import upload_to_s3

# testing deployment
application = Flask(__name__)

@application.route('/', methods=['GET'])
def index():
    return render_template('upload.html')

@application.route('/upload', methods=['POST'])
def upload_file():
    if 'resume' not in request.files:
        return "No file uploaded", 400
        
    file = request.files['resume']
    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return "Invalid file type. Please upload a PDF file.", 400

    try:
        print(f"[System] Uploading {file.filename} to S3...")
        s3_key = upload_to_s3(file, file.filename)
        print(f"[System] S3 Upload complete: {s3_key}")

        return """
        <div style="font-family: system-ui, -apple-system, sans-serif; text-align: center; margin-top: 80px; color: #333;">
            <h2 style="color: #28a745; font-size: 2rem;">Success! 🎉</h2>
            <p style="font-size: 1.1rem;">Your resume has been uploaded successfully.</p>
            <p style="color: #6c757d;">Our AI pipeline is now generating your portfolio and committing it to GitHub. This usually takes a few minutes.</p>
            
            <div style="margin-top: 35px; display: flex; justify-content: center; align-items: center; gap: 25px;">
                <a href="https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME" target="_blank" style="background-color: #24292e; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600; transition: background-color 0.2s;">
                    View GitHub Repository ↗
                </a>
                <a href="/" style="color: #007bff; text-decoration: none; font-weight: 500;">
                    ← Upload another file
                </a>
            </div>
        </div>
    """
    except Exception as e:
        print(f"[Error] Upload failed: {str(e)}")
        return f"An error occurred during processing: {str(e)}", 500

if __name__ == '__main__':
    # Enabled debug mode only during local execution
    is_dev = os.getenv("FLASK_ENV") == "development"
    application.run(debug=is_dev, port=5000)