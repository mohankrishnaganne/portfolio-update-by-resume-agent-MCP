import asyncio
from datetime import datetime, timezone

from google import genai
from google.genai import types

# Import from your mcp folder and your prompts.py file
from mcp_tools.github_client import GitHubMCPClient
from config import GEMINI_API_KEY
from prompts import HTML_PROMPT

def _convert_mcp_schema(schema: dict) -> dict:
    if not isinstance(schema, dict): return schema
    gemini_schema = {}
    if "type" in schema and isinstance(schema["type"], str):
        gemini_schema["type"] = schema["type"].upper()
    if "description" in schema: gemini_schema["description"] = schema["description"]
    if "properties" in schema:
        gemini_schema["properties"] = {k: _convert_mcp_schema(v) for k, v in schema["properties"].items()}
    if "items" in schema: gemini_schema["items"] = _convert_mcp_schema(schema["items"])
    if "required" in schema: gemini_schema["required"] = schema["required"]
    return gemini_schema


def inject_commit_metadata(html_content: str, timestamp: str | None = None) -> str:
    timestamp = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    marker = f'<meta name="portfolio-generated-at" content="{timestamp}">'

    if "<head" in html_content.lower():
        return html_content.replace("<head>", f"<head>\n{marker}", 1)
    if "<html" in html_content.lower():
        return html_content.replace("<html>", f"<html>\n{marker}", 1)
    return f"<!DOCTYPE html><html><head>{marker}</head><body>{html_content}</body></html>"


async def _run_agent_pipeline(resume_text: str, repo_name: str, file_path: str, github_username: str, resume_filename: str = "resume.pdf", upload_timestamp: str = None, s3_key: str = None) -> str:
    mcp_client = GitHubMCPClient()
    try:
        await mcp_client.connect()
        mcp_tools = await mcp_client.get_available_tools()
        
        gemini_tools = [
            types.FunctionDeclaration(
                name=t.name, 
                description=t.description, 
                parameters=_convert_mcp_schema(t.inputSchema)
            ) for t in mcp_tools
        ]
        gemini_tool_obj = types.Tool(function_declarations=gemini_tools)
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=HTML_PROMPT,
                tools=[gemini_tool_obj],
                temperature=0.1 
            )
        )
        
        # We explicitly force the AI to get the SHA first, then update
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

        MANDATORY ACTIONS IN EXACT ORDER:
        1. Use the 'get_file_contents' tool to check if '{file_path}' exists in the repo. If it does, extract the 'sha'.
        2. Generate the clean HTML portfolio.
        3. Use the 'create_or_update_file' tool to commit the HTML. If the file already existed, you MUST include the 'sha' parameter from step 1 to successfully update it.
           IMPORTANT: Use a meaningful commit message that includes the resume upload details:
           "Update portfolio from resume upload: {resume_filename} [{upload_timestamp}] - S3: {s3_key}"
        """
        
        print("[System] Waiting for AI response...")
        response = chat.send_message(user_instruction)
        
        # --- REMOVED THE FAULTY DEBUG PRINT HERE ---

        while True:
            function_calls = []
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        function_calls.append(part.function_call)
            
            if not function_calls: break
                
            for function_call in function_calls:
                tool_name = function_call.name
                tool_args = {k: v for k, v in function_call.args.items()} if hasattr(function_call.args, 'items') else dict(function_call.args)

                if tool_name == "create_or_update_file" and isinstance(tool_args.get("content"), str):
                    tool_args["content"] = inject_commit_metadata(tool_args["content"])
                
                try:
                    mcp_result = await mcp_client.call_tool(tool_name, tool_args)
                    content = "".join([part.text for part in mcp_result.content if part.type == "text"])
                except Exception as e:
                    content = f"Error: {str(e)}"
                
                # Send the tool execution result back to the AI
                response = chat.send_message(types.Part.from_function_response(name=tool_name, response={"result": content}))
        
        # Safely return text only when the loop finishes and tools are done
        try:
            return response.text
        except ValueError:
            return "AI finished processing."
    finally:
        await mcp_client.cleanup()

# Update the synchronous wrapper to accept the new parameters
def generate_and_commit_portfolio(resume_text: str, repo_name: str, file_path: str, github_username: str, resume_filename: str = "resume.pdf", upload_timestamp: str = None, s3_key: str = None) -> str:
    return asyncio.run(_run_agent_pipeline(resume_text, repo_name, file_path, github_username, resume_filename, upload_timestamp, s3_key))