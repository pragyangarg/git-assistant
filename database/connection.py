import os
from pathlib import Path
import aiosqlite


def get_db_path() -> Path:
    env_db = os.environ.get("DB_PATH")
    if env_db:
        path = Path(env_db)
    else:
        path = Path(__file__).resolve().parent.parent / "data" / "app.db"

    # Automatically create the parent directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


DB_PATH = get_db_path()


async def get_db():
    db_path = get_db_path()
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row

    await db.execute("PRAGMA foreign_keys = ON")

    return db
