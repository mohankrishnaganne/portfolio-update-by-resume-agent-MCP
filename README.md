# 🚀 Resume-to-Portfolio AI Pipeline

Transform your standard PDF resume into a fully deployed, beautiful GitHub portfolio website in seconds! 

This project leverages a Flask web interface, AWS S3 event triggers, containerized AWS Lambda functions, and the Model Context Protocol (MCP) to automate the entire process of reading a resume, designing a portfolio, and committing the code directly to a GitHub repository.

---

## ✨ How the Magic Works

1. **📄 Upload:** A user uploads their PDF resume via a sleek, modern web interface.
2. **🪣 Store:** The web app securely uploads the document to an AWS S3 bucket.
3. **⚡ Trigger:** The S3 upload instantly triggers a containerized AWS Lambda function.
4. **🧠 Process:** The Lambda AI Agent spins up, reads the PDF, and initializes a local GitHub MCP Server (safely operating within Lambda's `/tmp` directory).
5. **🌐 Deploy:** The AI agent translates your resume into portfolio code and pushes it directly to your live GitHub repository!

---

## 📂 Project Structure

The repository is divided into two main environments: the AWS Lambda backend (`lambda_agent`) and the user-facing web interface (`web_app`).

```text
PORTFOLIO-UPDATE-BY-RESUME/
├── lambda_agent/               # The AI Brain & AWS Serverless Backend
│   ├── mcp_tools/              # Model Context Protocol integrations
│   │   └── github_client.py    # Interfaces with the GitHub MCP server
│   ├── Services/               # Core backend services
│   │   ├── ai_agent_service.py # Orchestrates the AI logic
│   │   ├── pdf_service.py      # Parses uploaded resumes
│   │   ├── s3_service.py       # Handles S3 file downloading
│   │   └── upload_logger.py    # CloudWatch logging utilities
│   ├── tests/                  # Unit testing suite
│   ├── Dockerfile              # Containerizes the Lambda function & Node.js environment
│   ├── lambda_function.py      # The main AWS Lambda event handler
│   ├── prompts.py              # System instructions for the AI
│   └── requirements.txt        # Python dependencies for the Lambda environment
│
├── web_app/                    # The Frontend Flask Application
│   ├── static/                 # Static web assets
│   │   └── background_image.png 
│   ├── templates/              # HTML views
│   │   └── upload.html         # The glassmorphism upload UI
│   ├── application.py          # Main Flask server configuration
│   ├── config.py               # Web app configurations
│   ├── deploy.zip              # Packaged web app for deployment
│   ├── requirements.txt        # Python dependencies for the web server
│   └── s3_service.py           # Handles uploading the file from the web to S3
│
├── .env                        # Environment variables (Do not commit to version control!)
├── .gitignore                  
└── README.md                   
🛠️ Prerequisites
Before you begin, ensure you have the following accounts and tools set up:

AWS Account: With permissions to create S3 buckets, IAM Roles, ECR repositories, Elastic Beanstalk environments, and Lambda functions.

GitHub Account: A Personal Access Token (PAT) with repository permissions.

Docker: Installed on your local machine to build the Lambda container image.

Python 3.12+ Installed locally for web app testing.

AWS CLI: Installed and configured with your AWS credentials.

🚀 Getting Started & Deployment
1. Set Up Your Environment Variables
Create a .env file in the root directory and add the following necessary credentials:

Code snippet
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-resume-bucket-name

# GitHub Credentials
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_pat
GITHUB_USERNAME=your_username
2. Run the Web App Locally
Navigate to the web application folder, install dependencies, and start the Flask server:

Bash
cd web_app
pip install -r requirements.txt
python application.py
Visit http://localhost:5000 in your browser to see the upload UI.

3. Deploy the Web App to AWS Elastic Beanstalk
The web_app directory is ready to be hosted on AWS Elastic Beanstalk using a Python environment.

Compress the contents of the web_app folder (not the root folder itself, just the files inside web_app) into a .zip file (like the deploy.zip included in the repo).

Navigate to the Elastic Beanstalk console in AWS and create a new Web Server environment.

Select Python as the platform.

Upload your .zip file as the application code.

Go to the environment configuration settings and add your environment variables (from your .env file).

Deploy and wait for the health check to turn green!

4. Deploy the AI Agent to AWS Lambda (via Amazon ECR)
Because this agent relies on a Node.js MCP server running alongside Python, it must be deployed as a Docker container to AWS Lambda.

PowerShell Commands for ECR Deployment:
Ensure your AWS CLI is configured with your credentials before running these commands in Windows PowerShell. Replace YOUR_ACCOUNT_ID, us-east-1, and YOUR_ECR_REPO_NAME with your actual AWS details.

Authenticate Docker to your ECR registry:

PowerShell
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
Build the Docker Image:

PowerShell
cd lambda_agent
docker build -t portfolio-ai-agent .
Tag the Image:

PowerShell
docker tag portfolio-ai-agent:latest YOUR_ACCOUNT_[ID.dkr.ecr.us-east-1.amazonaws.com/YOUR_ECR_REPO_NAME:latest](https://ID.dkr.ecr.us-east-1.amazonaws.com/YOUR_ECR_REPO_NAME:latest)
Push to Amazon ECR:

PowerShell
docker push YOUR_ACCOUNT_[ID.dkr.ecr.us-east-1.amazonaws.com/YOUR_ECR_REPO_NAME:latest](https://ID.dkr.ecr.us-east-1.amazonaws.com/YOUR_ECR_REPO_NAME:latest)
Configure the Lambda Function:

In the AWS Console, create a new Lambda function selecting the Container Image option and choose your newly pushed ECR image.

Add an S3 ObjectCreated trigger to the function pointing to your resume upload bucket.

⚠️ CRITICAL: Go to Lambda Configuration -> General Configuration and increase the Memory to at least 1024 MB (Recommended 2048 MB). The MCP server and AI agent will run out of memory and time out on the default 128 MB setting! Add a timeout of at least 3-5 minutes.

💡 Technical Notes & Architecture Quirks
Read-Only Filesystem Bypass: AWS Lambda only allows write access to the /tmp directory. The AI Agent's connection logic dynamically reroutes npm and npx cache environments to /tmp to prevent startup crashes when executing the GitHub MCP server.

IAM Roles Over Hardcoded Keys: The Lambda function utilizes AWS IAM execution roles to read from S3, ensuring maximum security without hardcoding AWS keys into the container environment.