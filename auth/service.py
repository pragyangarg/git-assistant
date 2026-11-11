from database.repository import get_user_by_auth_subject


class AuthenticationError(Exception):
    pass


async def get_authenticated_user(auth_subject: str):
    """
    Convert the external authentication subject
    into our internal database user.
    """

    user = await get_user_by_auth_subject(auth_subject)

    if user is None:
        raise AuthenticationError(
            "Authenticated user is not registered."
        )

    return user