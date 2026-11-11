from fastmcp.server.dependencies import get_access_token


class AuthenticationError(Exception):
    pass


def get_authenticated_subject() -> str:
    token = get_access_token()

    if token is None:
        raise AuthenticationError(
            "Authentication required."
        )

    if not token.subject:
        raise AuthenticationError(
            "Authenticated token does not contain a subject."
        )

    return token.subject