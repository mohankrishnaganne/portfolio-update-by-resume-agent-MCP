import asyncio
import json
from datetime import datetime, timezone

from google import genai
from google.genai import types

# Import from your mcp folder and your prompts.py file
from mcp_tools.github_client import GitHubMCPClient
from config import GEMINI_API_KEY
from prompts import HTML_PROMPT


def inject_commit_metadata(html_content: str, timestamp: str | None = None) -> str:
    timestamp = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    marker = f'<meta name="portfolio-generated-at" content="{timestamp}">'

    if "<head" in html_content.lower():
        return html_content.replace("<head>", f"<head>\n{marker}", 1)
    if "<html" in html_content.lower():
        return html_content.replace("<html>", f"<html>\n{marker}", 1)
    return f"<!DOCTYPE html><html><head>{marker}</head><body>{html_content}</body></html>"


def _extract_ai_text(response) -> str:
    if getattr(response, "text", None):
        return response.text
    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        return "".join(part.text or "" for part in response.candidates[0].content.parts)
    return ""


async def _run_agent_pipeline(resume_text: str, repo_name: str, file_path: str, github_username: str, resume_filename: str = "resume.pdf", upload_timestamp: str = None, s3_key: str = None) -> str:
    mcp_client = GitHubMCPClient()
    try:
        await mcp_client.connect()

        client = genai.Client(api_key=GEMINI_API_KEY)
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=HTML_PROMPT,
                temperature=0.1
            )
        )

        user_instruction = f"""
        My GitHub username is '{github_username}'.
        Repo: '{repo_name}'
        File: '{file_path}'
        Branch: 'main'

        Resume Upload Information:
        - Filename: '{resume_filename}'
        - Upload Timestamp: '{upload_timestamp}'
        - S3 Location: '{s3_key}'

        Resume text:
        {resume_text}

        Generate only the complete HTML portfolio content as a single HTML document.
        """

        print("[System] Waiting for AI response...")
        response = chat.send_message(user_instruction)
        html_output = _extract_ai_text(response).strip()

        if not html_output:
            raise ValueError("AI did not return any portfolio HTML content.")

        final_html = inject_commit_metadata(html_output, timestamp=upload_timestamp)

        sha = None
        try:
            file_result = await mcp_client.call_tool("get_file_contents", {
                "owner": github_username,
                "repo": repo_name,
                "path": file_path,
                "branch": "main"
            })
            file_json = "".join(part.text for part in file_result.content if part.type == "text")
            file_data = json.loads(file_json)
            sha = file_data.get("sha")
            print(f"[System] Existing file SHA found: {sha}")
        except Exception as e:
            print(f"[System] File does not exist yet or SHA fetch failed: {e}")

        commit_args = {
            "owner": github_username,
            "repo": repo_name,
            "path": file_path,
            "content": final_html,
            "message": f"Update portfolio from resume upload: {resume_filename} [{upload_timestamp}] - S3: {s3_key}",
            "branch": "main"
        }
        if sha:
            commit_args["sha"] = sha

        commit_result = await mcp_client.call_tool("create_or_update_file", commit_args)
        print("[System] Portfolio commit complete.")
        return "Portfolio committed successfully."
    finally:
        await mcp_client.cleanup()


# Update the synchronous wrapper to accept the new parameters
def generate_and_commit_portfolio(resume_text: str, repo_name: str, file_path: str, github_username: str, resume_filename: str = "resume.pdf", upload_timestamp: str = None, s3_key: str = None) -> str:
    return asyncio.run(_run_agent_pipeline(resume_text, repo_name, file_path, github_username, resume_filename, upload_timestamp, s3_key))