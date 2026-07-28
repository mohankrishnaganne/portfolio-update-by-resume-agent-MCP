import asyncio
import json
from datetime import datetime, timezone
import re
from google import genai
from google.genai import types

# Import from your mcp folder and your prompts.py file
from mcp_tools.github_client import GitHubMCPClient
from config import GEMINI_API_KEY
from prompts import HTML_PROMPT


def build_polished_portfolio_html(html_content: str) -> str:
    content = (html_content or "").strip()
    if not content:
        content = "<h1>Professional Portfolio</h1>"

    if "<html" not in content.lower():
        content = f"<!DOCTYPE html><html><body>{content}</body></html>"

    if "<head" not in content.lower():
        content = content.replace("<html>", "<html><head>", 1)
        content = content.replace("</html>", "</head></html>", 1)

    style_block = """
    <style>
      :root {
        color-scheme: dark;
        --bg: #060b14;
        --bg-2: #14233b;
        --panel: rgba(8, 16, 30, 0.88);
        --panel-2: rgba(20, 38, 62, 0.95);
        --text: #f4f8ff;
        --muted: #aab8d1;
        --accent: #62e0d3;
        --accent-2: #84a7ff;
        --border: rgba(255,255,255,0.12);
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: 'Inter', 'Segoe UI', sans-serif;
        background:
          radial-gradient(circle at 10% 20%, rgba(98, 224, 211, 0.28), transparent 28%),
          radial-gradient(circle at 90% 15%, rgba(132, 167, 255, 0.24), transparent 24%),
          radial-gradient(circle at 50% 100%, rgba(255, 255, 255, 0.10), transparent 30%),
          linear-gradient(135deg, #060b14 0%, #10213a 40%, #172d49 70%, #203a56 100%);
        background-attachment: fixed;
        color: var(--text);
        line-height: 1.6;
      }
      .portfolio-shell {
        min-height: 100vh;
        padding: 32px 20px;
        display: flex;
        justify-content: center;
        align-items: center;
      }
      .portfolio-card {
        width: min(1100px, 100%);
        background: linear-gradient(145deg, var(--panel), var(--panel-2));
        border: 1px solid var(--border);
        border-radius: 28px;
        box-shadow: 0 24px 70px rgba(0, 0, 0, 0.38), 0 0 0 1px rgba(255,255,255,0.04) inset;
        overflow: hidden;
        backdrop-filter: blur(22px);
      }
      .portfolio-card > * { padding: 0 32px; }
      .portfolio-card h1,
      .portfolio-card h2,
      .portfolio-card h3 {
        margin-top: 0;
        color: #ffffff;
        letter-spacing: -0.02em;
      }
      .portfolio-card h1 {
        font-size: clamp(2rem, 4vw, 3rem);
        margin-bottom: 8px;
        font-weight: 700;
      }
      .portfolio-card h2 {
        font-size: 1.15rem;
        font-weight: 600;
        margin-bottom: 8px;
      }
      .portfolio-card p,
      .portfolio-card li {
        color: var(--muted);
        font-size: 1rem;
      }
      .portfolio-card a {
        color: var(--accent);
        text-decoration: none;
      }
      .portfolio-card ul {
        padding-left: 18px;
      }
      .portfolio-card section {
        padding-top: 28px;
        padding-bottom: 28px;
        border-bottom: 1px solid var(--border);
        transition: transform 180ms ease, background-color 180ms ease;
        position: relative;
      }
      .portfolio-card section::before {
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        width: 100%;
        height: 1px;
        background: linear-gradient(90deg, rgba(98,224,211,0.35), transparent);
        opacity: 0.6;
      }
      .portfolio-card section:hover {
        transform: translateY(-1px);
        background: rgba(255,255,255,0.02);
      }
      .portfolio-card section:last-child { border-bottom: none; }
      .portfolio-card .hero {
        padding-top: 36px;
        padding-bottom: 36px;
        background: linear-gradient(90deg, rgba(98, 224, 211, 0.16), rgba(132, 167, 255, 0.16));
        border-bottom: 1px solid rgba(255,255,255,0.08);
        position: relative;
        overflow: hidden;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 20px;
      }
      .portfolio-card .hero-title {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .portfolio-card .hero-title .eyebrow {
        display: inline-flex;
        width: fit-content;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.14);
        color: #dff8f5;
        font-size: 0.78rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
      }
      .portfolio-card .hero::after {
        content: "";
        position: absolute;
        inset: auto -20% -25% auto;
        width: 280px;
        height: 280px;
        background: radial-gradient(circle, rgba(98,224,211,0.2), transparent 70%);
        pointer-events: none;
      }
      .portfolio-card .hero .hero-badge {
        padding: 8px 14px;
        border-radius: 999px;
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.14);
        color: #dff9f6;
        font-size: 0.9rem;
        white-space: nowrap;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
      }
      .portfolio-card .hero .hero-meta {
        color: var(--muted);
        font-size: 0.95rem;
        max-width: 420px;
      }
      .portfolio-card .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 14px;
      }
      .portfolio-card .chip {
        display: inline-block;
        padding: 7px 12px;
        border-radius: 999px;
        background: rgba(255,255,255,0.08);
        color: #e9f4ff;
        border: 1px solid rgba(255,255,255,0.18);
        font-size: 0.9rem;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
        transition: transform 180ms ease, border-color 180ms ease;
      }
      .portfolio-card .chip:hover {
        transform: translateY(-1px);
        border-color: rgba(98,224,211,0.5);
      }
      .portfolio-card .footer {
        padding-top: 24px;
        padding-bottom: 28px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        color: var(--muted);
        font-size: 0.95rem;
      }
      .portfolio-card .footer .footer-links {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
      }
      .portfolio-card .footer .footer-links a {
        color: #dff8f5;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.12);
      }
      .portfolio-card .accent-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--accent), var(--accent-2));
        margin-right: 8px;
        box-shadow: 0 0 0 4px rgba(98,224,211,0.12);
      }
      @media (max-width: 700px) {
        .portfolio-card > * { padding: 0 20px; }
        .portfolio-shell { padding: 16px 10px; }
        .portfolio-card .hero { flex-direction: column; align-items: flex-start; }
        .portfolio-card .hero .hero-meta { max-width: 100%; }
      }
    </style>
    """

    if "<style" not in content.lower():
        if "</head>" in content.lower():
            content = content.replace("</head>", f"{style_block}</head>", 1)
        else:
            content = content.replace("<html>", "<html><head>" + style_block + "</head>", 1)

    body_match = re.search(r"<body[^>]*>(.*?)</body>", content, re.IGNORECASE | re.DOTALL)
    if body_match:
        body_content = body_match.group(1).strip()
        if "portfolio-shell" not in body_content.lower():
            footer_html = """
            <footer class="footer">
              <span><span class="accent-dot"></span>Available for data engineering and analytics opportunities</span>
              <div class="footer-links">
                <a href="#top">Top</a>
                <a href="#skills">Skills</a>
                <a href="#experience">Experience</a>
              </div>
            </footer>
            """
            wrapped_body = (
                "<main class=\"portfolio-shell\">\n"
                "  <div class=\"portfolio-card\">\n"
                f"{body_content}\n"
                f"{footer_html}\n"
                "  </div>\n"
                "</main>"
            )
            content = content.replace(body_match.group(0), f"<body>\n{wrapped_body}\n</body>", 1)
    else:
        content = content.replace("<body>", "<body><main class=\"portfolio-shell\"><div class=\"portfolio-card\">", 1)
        content = content.replace("</body>", "</div></main></body>", 1)

    return content

def inject_commit_metadata(html_content: str, timestamp: str | None = None) -> str:
    timestamp = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    marker = f'<meta name="portfolio-generated-at" content="{timestamp}">'

    if "<head" in html_content.lower():
        updated_html = html_content.replace("<head>", f"<head>\n{marker}", 1)
    elif "<html" in html_content.lower():
        updated_html = html_content.replace("<html>", f"<html>\n{marker}", 1)
    else:
        updated_html = f"<!DOCTYPE html><html><head>{marker}</head><body>{html_content}</body></html>"

    return build_polished_portfolio_html(updated_html)


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