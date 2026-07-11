import asyncio
from google import genai
from google.genai import types

from mcp_client import GitHubMCPClient
from config import GEMINI_API_KEY
from prompts import SYSTEM_PROMPT

def convert_mcp_schema_to_gemini(schema: dict) -> dict:
    """
    Recursively translates a standard JSON schema into the strict format 
    expected by the Google GenAI SDK (uppercase types, stripped extra fields).
    """
    if not isinstance(schema, dict):
        return schema

    gemini_schema = {}
    
    # 1. Convert lowercase types to uppercase (e.g., 'object' -> 'OBJECT')
    if "type" in schema and isinstance(schema["type"], str):
        gemini_schema["type"] = schema["type"].upper()

    # 2. Keep descriptions if they exist
    if "description" in schema:
        gemini_schema["description"] = schema["description"]
        
    # 3. Recursively convert nested properties
    if "properties" in schema:
        gemini_schema["properties"] = {
            k: convert_mcp_schema_to_gemini(v) 
            for k, v in schema["properties"].items()
        }
        
    # 4. Handle arrays
    if "items" in schema:
        gemini_schema["items"] = convert_mcp_schema_to_gemini(schema["items"])
        
    # 5. Keep required fields lists
    if "required" in schema:
        gemini_schema["required"] = schema["required"]
        
    return gemini_schema

async def main():
    mcp_client = GitHubMCPClient()
    try:
        # 1. Connect to MCP Server
        await mcp_client.connect()
        
        # 2. Discover Tools
        mcp_tools = await mcp_client.get_available_tools()
        
        # 3. Translate MCP Tools to Gemini format
        gemini_tools = []
        for tool in mcp_tools:
            # Clean the MCP schema to match Gemini's strict expectations
            clean_schema = convert_mcp_schema_to_gemini(tool.inputSchema)
            
            gemini_tools.append(
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=clean_schema
                )
            )
            
        gemini_tool_obj = types.Tool(function_declarations=gemini_tools)
        
        # 4. Initialize LLM Agent
        client = genai.Client(api_key=GEMINI_API_KEY)
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[gemini_tool_obj],
                temperature=0.0 # Keep it deterministic for tool calling
            )
        )
        
        print("🤖 Agent is ready! (Type 'exit' to quit)")
        owner_name = input("To help me out, what is your exact GitHub username? ")
        
        # Pre-seed the chat with the owner context
        chat.send_message(f"For context, my GitHub username is: {owner_name}")
        
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() == 'exit':
                break
                
            # Send message to LLM
            response = chat.send_message(user_input)
            
            # 5. Handle Agent Tool Calls
            while True:
                # Safely find any function calls in the nested response parts
                function_calls = []
                if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.function_call:
                            function_calls.append(part.function_call)
                
                # If no tools were called, exit the loop and print the text response
                if not function_calls:
                    break
                    
                for function_call in function_calls:
                    tool_name = function_call.name
                    
                    # Safely parse args (handles both dicts and protobuf maps)
                    if hasattr(function_call.args, 'items'):
                        tool_args = {k: v for k, v in function_call.args.items()}
                    else:
                        tool_args = dict(function_call.args) if function_call.args else {}
                    
                    try:
                        # Execute against GitHub
                        mcp_result = await mcp_client.call_tool(tool_name, tool_args)
                        
                        # Extract the result text
                        content = ""
                        for part in mcp_result.content:
                            if part.type == "text":
                                content += part.text + "\n"
                    except Exception as e:
                        content = f"Error executing tool {tool_name}: {str(e)}"
                    
                    # Send the result back to the LLM so it knows what happened
                    response = chat.send_message(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"result": content}
                        )
                    )
            
            # Print the final human-readable response
            print(f"\nAgent: {response.text}")
            
    finally:
        await mcp_client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())