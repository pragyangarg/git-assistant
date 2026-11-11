from .connection import get_db


async def create_user(
    auth_subject: str,
    name: str,
    email: str
):
    db = await get_db()

    try:
        cursor = await db.execute(
            """
            INSERT INTO users (
                auth_subject,
                name,
                email
            )
            VALUES (?, ?, ?)
            ON CONFLICT(auth_subject) DO UPDATE SET
                name = excluded.name,
                email = excluded.email
            """,
            (auth_subject, name, email)
        )

        await db.commit()

        # Get the user's ID regardless of whether
        # the row was newly inserted or already existed.
        cursor = await db.execute(
            """
            SELECT id
            FROM users
            WHERE auth_subject = ?
            """,
            (auth_subject,)
        )

        user = await cursor.fetchone()

        return user["id"]

    finally:
        await db.close()


async def get_user_by_email(email: str):
    db = await get_db()

    try:
        cursor = await db.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        )

        return await cursor.fetchone()

    finally:
        await db.close()


async def get_user_by_auth_subject(auth_subject: str):
    db = await get_db()

    try:
        cursor = await db.execute(
            """
            SELECT *
            FROM users
            WHERE auth_subject = ?
            """,
            (auth_subject,)
        )

        return await cursor.fetchone()

    finally:
        await db.close()


async def add_repository(
    user_id: int,
    name: str,
    path: str
):
    db = await get_db()

    try:
        cursor = await db.execute(
            """
            INSERT INTO repositories
                (user_id, name, path)
            VALUES (?, ?, ?)
            """,
            (user_id, name, path)
        )

        await db.commit()

        return cursor.lastrowid

    finally:
        await db.close()


async def get_user_repositories(user_id: int):
    db = await get_db()

    try:
        cursor = await db.execute(
            """
            SELECT id, name, path
            FROM repositories
            WHERE user_id = ?
            """,
            (user_id,)
        )

        return await cursor.fetchall()

    finally:
        await db.close()


async def get_repository_for_user(
    repository_id: int,
    user_id: int
):
    db = await get_db()

    try:
        cursor = await db.execute(
            """
            SELECT id, user_id, name, path, created_at
            FROM repositories
            WHERE id = ?
              AND user_id = ?
            """,
            (repository_id, user_id)
        )

        return await cursor.fetchone()

    finally:
        await db.close()