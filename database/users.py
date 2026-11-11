from .connection import get_db


async def get_or_create_user(
    auth_subject: str,
    name: str,
    email: str,
) -> int:

    db = await get_db()

    try:
        cursor = await db.execute(
            """
            SELECT id
            FROM users
            WHERE auth_subject = ?
            """,
            (auth_subject,),
        )

        user = await cursor.fetchone()

        if user:
            return user["id"]

        cursor = await db.execute(
            """
            INSERT INTO users (
                auth_subject,
                name,
                email
            )
            VALUES (?, ?, ?)
            """,
            (
                auth_subject,
                name,
                email,
            ),
        )

        await db.commit()

        return cursor.lastrowid

    finally:
        await db.close()