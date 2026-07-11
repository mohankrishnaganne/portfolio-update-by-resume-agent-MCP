import os
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from config import MCP_SERVER_COMMAND, MCP_SERVER_ARGS, GITHUB_TOKEN

logger = logging.getLogger("mcp_client")

class GitHubMCPClient:
    """Manages life-cycle connections and interactions with the GitHub MCP Server."""
    
    def __init__(self):
        # Build clean environment map
        server_env = dict(os.environ)
        
        # INJECT BOTH KEYS SOUGHT BY THE SERVER IMPLEMENTATION
        server_env["GITHUB_TOKEN"] = GITHUB_TOKEN
        server_env["GITHUB_PERSONAL_ACCESS_TOKEN"] = GITHUB_TOKEN
        
        self.server_parameters = StdioServerParameters(
            command=MCP_SERVER_COMMAND,
            args=MCP_SERVER_ARGS,
            env=server_env
        )
        self._session: ClientSession | None = None

    @asynccontextmanager
    async def connect(self):
        """Asynchronous context manager to manage server connections securely."""
        logger.info("Spawning and connecting to GitHub MCP Server...")
        async with stdio_client(self.server_parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                self._session = session
                logger.info("MCP Session established successfully.")
                try:
                    yield self
                finally:
                    self._session = None
                    logger.info("MCP Session closed safely.")

    async def fetch_available_tools(self) -> List[Any]:
        if not self._session:
            raise RuntimeError("Client is not connected to an active session.")
        tool_result = await self._session.list_tools()
        return tool_result.tools

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if not self._session:
            raise RuntimeError("Client is not connected to an active session.")
        
        logger.info(f"Invoking tool: {tool_name} with args: {arguments}")
        try:
            response = await self._session.call_tool(tool_name, arguments=arguments)
            return response
        except Exception as e:
            logger.error(f"Failed to execute tool {tool_name}: {str(e)}")
            raise e