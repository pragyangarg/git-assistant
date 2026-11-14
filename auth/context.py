from fastmcp.server.dependencies import get_access_token, get_http_headers


class AuthenticationError(Exception):
    pass


def get_horizon_actor() -> dict | None:
    """
    Return the FastMCP Gateway (Horizon) actor context, if present.

    On FastMCP Cloud the gateway authenticates the caller and forwards
    trusted actor-context headers (it strips any client-supplied
    `horizon-*` headers first). Local/self-hosted runs have no gateway,
    so this returns None.
    """

    try:
        headers = get_http_headers() or {}
    except Exception:
        headers = {}

    actor = headers.get("horizon-actor")

    if not actor:
        return None

    return {
        "id": actor,
        "type": headers.get("horizon-actor-type"),
        "email": headers.get("horizon-actor-email"),
        "organization_role": headers.get("horizon-user-role"),
        "server_roles": headers.get("horizon-server-roles"),
    }


def _subject_from_claims(claims: dict | None) -> str | None:
    claims = claims or {}

    for key in ("sub", "login", "github_id", "id"):
        value = claims.get(key)
        if value:
            return str(value)

    return None


def get_authenticated_subject() -> str:
    actor = get_horizon_actor()

    if actor:
        return actor["id"]

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


def get_identity_hints() -> dict:
    """Best-effort name/email for just-in-time user provisioning."""

    actor = get_horizon_actor()

    if actor:
        email = actor.get("email")
        name = email.split("@")[0] if email else None
        return {"name": name, "email": email}

    token = get_access_token()

    if token is None:
        return {"name": None, "email": None}

    claims = getattr(token, "claims", None) or {}

    return {
        "name": claims.get("name") or claims.get("login"),
        "email": claims.get("email"),
    }
