from .connection import get_db


async def init_db():
    db = await get_db()

    try:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auth_subject TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)

        # Seed mock users if empty so authorization works out of the box
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        count = row[0] if row else 0

        if count == 0:
            await db.execute("""
                INSERT OR IGNORE INTO users (auth_subject, name, email)
                VALUES 
                    ('auth0|alice', 'Alice', 'alice@test.com'),
                    ('auth0|bob', 'Bob', 'bob@test.com'),
                    ('auth0|alice_db', 'Alice', 'alice@example.com'),
                    ('auth0|bob_db', 'Bob', 'bob@example.com')
            """)
            await db.commit()

            # Seed repositories for user 1 & 2
            cursor_u1 = await db.execute("SELECT id FROM users WHERE auth_subject = 'auth0|alice'")
            u1 = await cursor_u1.fetchone()
            if u1:
                u1_id = u1[0]
                await db.execute("""
                    INSERT INTO repositories (user_id, name, path)
                    VALUES 
                        (?, 'alice-project', '/repos/alice-project'),
                        (?, 'food-savr', '/repos/alice/food-savr')
                """, (u1_id, u1_id))

            cursor_u2 = await db.execute("SELECT id FROM users WHERE auth_subject = 'auth0|bob'")
            u2 = await cursor_u2.fetchone()
            if u2:
                u2_id = u2[0]
                await db.execute("""
                    INSERT INTO repositories (user_id, name, path)
                    VALUES (?, 'bob-project', '/repos/bob-project')
                """, (u2_id,))

        await db.commit()

    finally:
        await db.close()
