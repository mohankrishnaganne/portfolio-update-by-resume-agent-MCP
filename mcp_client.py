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
        """Spins up the GitHub MCP server and establishes a connection."""
        print("[System] Connecting to GitHub MCP Server...")
        
        # We must pass the current OS environment to the subprocess 
        # so it has access to GITHUB_PERSONAL_ACCESS_TOKEN and the Node PATH.
        env = os.environ.copy()
        
        # Windows requires the .cmd extension for npx
        npx_command = "npx.cmd" if sys.platform == "win32" else "npx"
        
        server_params = StdioServerParameters(
            command=npx_command,
            args=["-y", "@modelcontextprotocol/server-github"],
            env=env
        )
        
        # Initialize standard IO transport
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.read, self.write = stdio_transport
        
        # Create and initialize the session
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.read, self.write))
        await self.session.initialize()
        print("[System] Successfully connected to GitHub MCP Server.\n")

    async def get_available_tools(self) -> List[Any]:
        """Asks the MCP server for a list of capabilities."""
        response = await self.session.list_tools()
        return response.tools

    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """Sends an execution request to the MCP server."""
        print(f"\n[MCP Executing] 🛠️  {tool_name}...")
        result = await self.session.call_tool(tool_name, arguments=tool_args)
        return result

    async def cleanup(self):
        """Gracefully closes the connection."""
        await self.exit_stack.aclose()