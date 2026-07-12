import os
import sys
from typing import Any, Dict, List
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class GitHubMCPClient:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.session: ClientSession | None = None

    async def connect(self):
        print("[System] Connecting to GitHub MCP Server...")
        env = os.environ.copy()
        
        # Bulletproof Windows execution using cmd.exe
        if sys.platform == "win32":
            command = "cmd.exe"
            args = ["/c", "npx", "-y", "@modelcontextprotocol/server-github"]
        else:
            command = "npx"
            args = ["-y", "@modelcontextprotocol/server-github"]
        
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.read, self.write = stdio_transport
        
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.read, self.write))
        await self.session.initialize()
        print("[System] Successfully connected to GitHub MCP Server.\n")

    async def get_available_tools(self) -> List[Any]:
        response = await self.session.list_tools()
        return response.tools

    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        print(f"\n[MCP Executing] 🛠️  {tool_name}...")
        result = await self.session.call_tool(tool_name, arguments=tool_args)
        return result

    async def cleanup(self):
        await self.exit_stack.aclose()