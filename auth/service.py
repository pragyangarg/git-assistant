from database.repository import (
    create_user,
    get_user_by_auth_subject,
)


class AuthenticationError(Exception):
    pass


async def get_authenticated_user(
    auth_subject: str,
    name: str | None = None,
    email: str | None = None,
):
    """
    Convert the external authentication subject
    into our internal database user.

    The hosted database is ephemeral (rebuilt on every deployment),
    so users are provisioned just-in-time on their first authenticated
    call instead of requiring a manual seed. Name/email come from the
    identity provider's claims; if they are not public they fall back
    to derived values so the NOT NULL / UNIQUE constraints hold.
    """

    user = await get_user_by_auth_subject(auth_subject)

    if user is not None:
        return user

    fallback_name = name or f"user-{auth_subject}"
    fallback_email = email or f"{auth_subject}@users.noreply.local"

    try:
        await create_user(auth_subject, fallback_name, fallback_email)
    except Exception as e:
        raise AuthenticationError(
            f"Authenticated user is not registered and could not be created: {e}"
        ) from e

    user = await get_user_by_auth_subject(auth_subject)

    if user is None:
        raise AuthenticationError(
            "Authenticated user is not registered."
        )

    return user
