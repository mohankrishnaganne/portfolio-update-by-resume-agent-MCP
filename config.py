import os
from dotenv import load_dotenv

# Load workspace environment configurations
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Accept either environment variable configuration name
GITHUB_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN")

if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in environment variables.")
if not GITHUB_TOKEN:
    raise ValueError("Missing GITHUB_TOKEN or GITHUB_PERSONAL_ACCESS_TOKEN in environment variables.")

MCP_SERVER_COMMAND = "npx"
MCP_SERVER_ARGS = ["-y", "@modelcontextprotocol/server-github"]