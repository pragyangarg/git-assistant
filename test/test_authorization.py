import asyncio

from database.schema import init_db
from database.repository import (
    create_user,
    add_repository,
)
from auth.authorization import (
    authorize_repository,
    AuthorizationError,
)


async def main():

    await init_db()

    alice_id = await create_user(
        "auth0|alice",
        "Alice",
        "alice@test.com",
    )

    bob_id = await create_user(
        "auth0|bob",
        "Bob",
        "bob@test.com",
    )

    alice_repo = await add_repository(
        alice_id,
        "alice-project",
        "/repos/alice-project",
    )

    bob_repo = await add_repository(
        bob_id,
        "bob-project",
        "/repos/bob-project",
    )

    # Alice accessing her own repository
    repo = await authorize_repository(
        alice_id,
        alice_repo,
    )

    print("Alice → Alice repo:", dict(repo))

    # Alice attempting to access Bob's repository
    try:
        await authorize_repository(
            alice_id,
            bob_repo,
        )

        print("SECURITY BUG!")

    except AuthorizationError:
        print("Alice → Bob repo: ACCESS DENIED")


if __name__ == "__main__":
    asyncio.run(main())