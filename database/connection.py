import aiosqlite
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row

    await db.execute("PRAGMA foreign_keys = ON")

    return db
