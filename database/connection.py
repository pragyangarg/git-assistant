import aiosqlite
from pathlib import Path

# FastMCP Cloud application filesystem is read-only.
# /tmp is writable during the running container.
DB_PATH = Path("/tmp") / "app.db"


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row

    await db.execute("PRAGMA foreign_keys = ON")

    return db