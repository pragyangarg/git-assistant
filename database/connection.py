import os
import tempfile
from pathlib import Path
import aiosqlite


def get_db_path() -> Path:
    env_db = os.environ.get("DB_PATH")
    if env_db:
        path = Path(env_db)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    # Local project data path
    local_path = Path(__file__).resolve().parent.parent / "data" / "app.db"
    try:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        # Test if the directory is writable
        test_file = local_path.parent / ".writable_test"
        test_file.touch()
        test_file.unlink()
        return local_path
    except (OSError, PermissionError):
        # In cloud environments where container root /app is read-only, use tempfile dir
        cloud_path = Path(tempfile.gettempdir()) / "git_assistant_app.db"
        return cloud_path


DB_PATH = get_db_path()


async def get_db():
    db_path = get_db_path()
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row

    await db.execute("PRAGMA foreign_keys = ON")

    return db
