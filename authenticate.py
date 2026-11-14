"""
One-time interactive OAuth login helper.
Run this script in terminal once to authenticate with GitHub in your browser.
The obtained tokens will be saved to ~/.mcp-git-assistant/tokens so Claude Desktop
and MCP Inspector can use them immediately.
"""
import asyncio
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

TOKEN_DIR = Path.home() / ".mcp-git-assistant" / "tokens"
TOKEN_DIR.mkdir(parents=True, exist_ok=True)

async def main():
    print(f"Connecting to remote MCP server: {REMOTE_MCP_URL}")
    print("If not already authenticated, your default browser will open automatically for GitHub authorization...")

    store = DiskStore(directory=str(TOKEN_DIR))
    oauth_provider = OAuth(
        mcp_url=REMOTE_MCP_URL,
        token_storage=store,
        client_name="Claude Desktop Git Assistant",
        additional_client_metadata={"token_endpoint_auth_method": "client_secret_post"},
    )

    client = fastmcp.Client(
        transport=REMOTE_MCP_URL,
        auth=oauth_provider,
    )

    async with client:
        tools = await client.list_tools()
        print("\n✅ Successfully authenticated!")
        print(f"✅ Discovered {len(tools)} tools:")
        for t in tools:
            print(f"  - {t.name}: {t.description}")
        print(f"\nOAuth tokens are saved to {TOKEN_DIR}.")
        print("You can now open/reload Claude Desktop and all tools will be available!")

if __name__ == "__main__":
    asyncio.run(main())
