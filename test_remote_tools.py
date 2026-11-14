"""
End-to-end smoke test: connect to the remote MCP server with the
persisted OAuth tokens and call every tool.
"""
import asyncio
import json
import os
import sys

import fastmcp
from fastmcp.client.auth.oauth import OAuth
from dotenv import load_dotenv

from token_store import create_token_store

load_dotenv()

REMOTE_MCP_URL = os.environ.get("BASE_URL", "https://retired-lime-bat.fastmcp.app")
if not REMOTE_MCP_URL.endswith("/mcp"):
    REMOTE_MCP_URL = f"{REMOTE_MCP_URL.rstrip('/')}/mcp"


def show(name, result):
    try:
        data = json.loads(result.content[0].text)
    except Exception:
        data = result.content[0].text if result.content else str(result)
    print(f"\n=== {name} ===")
    print(data if isinstance(data, str) else json.dumps(data, indent=2)[:2000])


async def main():
    oauth = OAuth(
        mcp_url=REMOTE_MCP_URL,
        token_storage=create_token_store(),
        client_name="Claude Desktop Git Assistant",
        additional_client_metadata={"token_endpoint_auth_method": "client_secret_post"},
    )

    async with fastmcp.Client(transport=REMOTE_MCP_URL, auth=oauth, timeout=60) as client:
        tools = await client.list_tools()
        print("Tools discovered:")
        for t in tools:
            print(f"  - {t.name}")

        async def run(label, name, args):
            try:
                show(label, await client.call_tool(name, args))
            except Exception as e:
                print(f"\n=== {label} ===\nERROR: {e}")

        await run("debug_auth", "debug_auth", {})
        await run("debug_github_user", "debug_github_user", {})
        await run("project_analysis", "project_analysis", {})
        await run("git_history", "git_history", {"repository": ".", "limit": 3})
        await run("search_code", "search_code", {"query": "FastMCP", "directory": "."})
        await run("read_file", "read_file", {"file_path": "server.py", "start_line": 1, "end_line": 10})
        await run("list_my_repositories", "list_my_repositories", {})
        await run("list_github_repositories", "list_github_repositories", {})


if __name__ == "__main__":
    asyncio.run(main())
