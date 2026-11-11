import asyncio

from database.schema import init_db
from database.repository import (
    create_user,
    get_user_by_email,
    add_repository,
    get_user_repositories,
)


async def main():
    await init_db()

    # Create users
    alice_id = await create_user(
        "auth0|alice_db",
        "Alice",
        "alice@example.com"
    )

    bob_id = await create_user(
        "auth0|bob_db",
        "Bob",
        "bob@example.com"
    )

    print("Alice ID:", alice_id)
    print("Bob ID:", bob_id)

    # Add repositories
    await add_repository(
        alice_id,
        "food-savr",
        "/repos/alice/food-savr"
    )

    await add_repository(
        alice_id,
        "active-arc",
        "/repos/alice/active-arc"
    )

    await add_repository(
        bob_id,
        "ecommerce",
        "/repos/bob/ecommerce"
    )

    # Fetch user
    user = await get_user_by_email(
        "alice@example.com"
    )

    print("\nAlice:")
    print(dict(user))

    # Fetch Alice's repositories
    repos = await get_user_repositories(alice_id)

    print("\nAlice's repositories:")

    for repo in repos:
        print(dict(repo))


if __name__ == "__main__":
    asyncio.run(main())