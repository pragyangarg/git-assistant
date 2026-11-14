"""
Persistent OAuth token storage for the MCP client.

FastMCP's TokenStorageAdapter stores OAuth tokens with
``ttl=tokens.expires_in`` (usually 3600 seconds). The disk store then
evicts the cache entry when it expires, which also destroys the
refresh token. The next client start finds nothing and forces a full
browser re-authorization.

This store ignores TTLs so the token entry persists across restarts.
Token expiry itself is still handled correctly: the MCP OAuth client
reads ``expires_in`` and refreshes the access token using the stored
refresh token when it is needed.
"""

from pathlib import Path

from key_value.aio.stores.disk import DiskStore

TOKEN_DIR = Path.home() / ".mcp-git-assistant" / "tokens"


class NoExpiryDiskStore(DiskStore):
    """DiskStore that never expires entries, preserving refresh tokens."""

    async def put(self, key, value, *, collection=None, ttl=None):
        # Drop the TTL entirely; diskcache keeps the entry forever.
        return await super().put(key, value, collection=collection, ttl=None)


def create_token_store() -> NoExpiryDiskStore:
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    return NoExpiryDiskStore(directory=str(TOKEN_DIR))
