import asyncio
import logging
import json
from typing import List, Dict, Any

from google import genai
from google.genai import types

from config import GEMINI_API_KEY
from prompts import SYSTEM_INSTRUCTION
from mcp_client import GitHubMCPClient

# Set up clean visual logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("agent")

class GeminiMCPAgent:
    def __init__(self, mcp_client: GitHubMCPClient):
        self.mcp_client = mcp_client
        # Instantiate the official Google GenAI SDK client
        self.ai_client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_name = "gemini-2.5-flash"

    def _clean_schema(self, schema: Any) -> Any:
        """
        Recursively traverses and purges schema keys that Gemini's 
        API validation layer does not accept.
        """
        if isinstance(schema, dict):
            cleaned = {}
            for k, v in schema.items():
                # Convert snake_case from Pydantic exports back or ignore them
                if k in ["additional_properties", "additionalProperties", "$schema"]:
                    continue
                
                # Gemini doesn't support complex anyOf/allOf in function declarations.
                # If seen, we simplify by defaulting to a generic string type description
                if k in ["anyOf", "allOf", "any_of", "all_of"]:
                    return {"type": "STRING"}
                    
                cleaned[k] = self._clean_schema(v)
            return cleaned
        elif isinstance(schema, list):
            return [self._clean_schema(item) for item in schema]
        return schema

    def _convert_mcp_to_gemini_tools(self, mcp_tools: List[Any]) -> List[types.Tool]:
        """
        Maps standard MCP tool schemas cleanly to Gemini's expected 
        types.Tool structure, running a deep structural cleanup.
        """
        gemini_tools = []
        for tool in mcp_tools:
            # Export raw schema dict from the MCP Tool model object
            raw_parameters = tool.inputSchema if isinstance(tool.inputSchema, dict) else getattr(tool.inputSchema, "model_dump", lambda: {})()
            
            # Deep clean the dictionary parameters
            cleaned_parameters = self._clean_schema(raw_parameters)
                
            # Construct the formal FunctionDeclaration model required by the SDK
            func_declaration = types.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=cleaned_parameters
            )
            
            # Wrap it inside the official Tool container class
            gemini_tools.append(types.Tool(function_declarations=[func_declaration]))
            
        return gemini_tools

    async def run(self, user_prompt: str):
        """Executes the agent logic over a conversation loop."""
        # 1. Fetch available capabilities via MCP server
        mcp_tools = await self.mcp_client.fetch_available_tools()
        gemini_tools = self._convert_mcp_to_gemini_tools(mcp_tools)
        
        logger.info(f"Loaded {len(gemini_tools)} tool definitions from MCP Server.")

        # Initialize conversation state tracking
        messages = [
            types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)])
        ]
        
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=gemini_tools,
            temperature=0.2, # Lower temperature for stable tool decisions
        )

        loop_active = True
        iterations = 0
        max_iterations = 10 # Circuit breaker against infinite loops

        while loop_active and iterations < max_iterations:
            iterations += 1
            logger.info("Sending context window state to Gemini...")
            
            # Send the entire thread history to the model
            response = self.ai_client.models.generate_content(
                model=self.model_name,
                contents=messages,
                config=config
            )

            # Append the model's turning response to history
            if response.candidates and response.candidates[0].content:
                model_content = response.candidates[0].content
                messages.append(model_content)
                
                # Check for explicit text responses
                if response.text:
                    print(f"\n[Agent Response]:\n{response.text}\n")

            # Check if the model opted to call a function/tool
            function_calls = response.function_calls
            if not function_calls:
                # No more tools requested, execution completed successfully
                logger.info("Agent execution completed successfully without further tool prompts.")
                loop_active = False
                break

            # Handle the requested tool calls sequentially
            tool_response_parts = []
            for call in function_calls:
                tool_name = call.name
                # Arguments map naturally from a struct or dict mapping
                args = dict(call.args) if call.args else {}
                
                print(f"🔨 [LLM requested tool execution]: {tool_name}")
                
                try:
                    # Route execution directly through our active MCP server transport
                    mcp_output = await self.mcp_client.execute_tool(tool_name, args)
                    
                    # Package content text arrays into standard strings
                    result_text = "\n".join([c.text for c in mcp_output.content if hasattr(c, 'text')])
                    print(f"✓ [Tool Output Success Summary]: Payload received from MCP server.")
                    
                    # Append response text mapped to function name
                    tool_response_parts.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"result": result_text}
                        )
                    )
                except Exception as e:
                    # Pass errors directly back to the model context to handle gracefully
                    tool_response_parts.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"error": str(e)}
                        )
                    )

            # Append complete execution updates back into user role context tracking loops
            messages.append(types.Content(role="user", parts=tool_response_parts))

async def main():
    prompt = "Create a public GitHub repository named mcp-demo-repo with a README containing 'Hello from MCP'."
    
    client = GitHubMCPClient()
    async with client.connect():
        agent = GeminiMCPAgent(client)
        await agent.run(prompt)

if __name__ == "__main__":
    asyncio.run(main())