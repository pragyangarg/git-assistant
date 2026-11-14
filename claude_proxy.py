"""
Claude Desktop MCP Client Proxy with GitHub OAuth.
Launches FastMCP as an stdio proxy connecting to the remote OAuth MCP server.
When launched by Claude Desktop, it will open the browser once for GitHub authentication
and persist the access/refresh token in ~/.mcp-git-assistant/tokens.
"""
from pathlib import Path
import os
from dotenv import load_dotenv

import fastmcp
from fastmcp.client.auth.oauth import OAuth
from key_value.aio.stores.disk import DiskStore

load_dotenv()

REMOTE_MCP_URL = os.environ.get("BASE_URL", "https://retired-lime-bat.fastmcp.app")
if not REMOTE_MCP_URL.endswith("/mcp"):
    REMOTE_MCP_URL = f"{REMOTE_MCP_URL.rstrip('/')}/mcp"

# Persistent token directory
TOKEN_DIR = Path.home() / ".mcp-git-assistant" / "tokens"
TOKEN_DIR.mkdir(parents=True, exist_ok=True)

store = DiskStore(directory=str(TOKEN_DIR))
oauth_provider = OAuth(
    mcp_url=REMOTE_MCP_URL,
    token_storage=store,
    client_name="Claude Desktop Git Assistant",
    additional_client_metadata={"token_endpoint_auth_method": "client_secret_post"},
)

remote_client = fastmcp.Client(
    transport=REMOTE_MCP_URL,
    auth=oauth_provider,
)

proxy_server = fastmcp.FastMCP.as_proxy(
    remote_client,
    name="GIT ASSISTANT",
)

if __name__ == "__main__":
    proxy_server.run(transport="stdio")
