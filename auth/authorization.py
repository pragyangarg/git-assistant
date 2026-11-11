from database.repository import get_repository_for_user


class AuthorizationError(Exception):
    pass


async def authorize_repository(
    user_id: int,
    repository_id: int,
):
    repository = await get_repository_for_user(
        repository_id=repository_id,
        user_id=user_id,
    )

    if repository is None:
        raise AuthorizationError(
            "You do not have access to this repository."
        )

    return repository