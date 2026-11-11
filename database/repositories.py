from .connection import get_db


async def get_repository_for_user(
    repository_id: int,
    user_id: int,
):
    db = await get_db()

    try:
        cursor = await db.execute(
            """
            SELECT id, user_id, name, path
            FROM repositories
            WHERE id = ?
              AND user_id = ?
            """,
            (repository_id, user_id),
        )

        return await cursor.fetchone()

    finally:
        await db.close()