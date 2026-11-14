from fastmcp.server.dependencies import get_access_token


class AuthenticationError(Exception):
    pass


def _subject_from_claims(claims: dict | None) -> str | None:
    claims = claims or {}

    for key in ("sub", "login", "github_id", "id"):
        value = claims.get(key)
        if value:
            return str(value)

    return None


def get_authenticated_subject() -> str:
    token = get_access_token()

    if token is None:
        raise AuthenticationError(
            "Authentication required."
        )

    # The GitHub auth provider returns an AccessToken without `subject`
    # set; the stable identity lives in the claims (`sub`/`login`).
    subject = token.subject or _subject_from_claims(
        getattr(token, "claims", None)
    )

    if not subject:
        raise AuthenticationError(
            "Authenticated token does not contain a subject."
        )

    return subject