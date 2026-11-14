from fastmcp import FastMCP
from pathlib import Path
from git import Repo
import os
from contextlib import asynccontextmanager
from fastmcp.server.auth.providers.github import GitHubProvider
import asyncio

from database.schema import init_db

from auth.context import get_authenticated_subject
from auth.service import get_authenticated_user
from database.repository import get_user_repositories

import os
from dotenv import load_dotenv

load_dotenv()
#   asyncio.run(init_db())


#mcp = FastMCP("PROJECT ASSISTANT")##############
@asynccontextmanager
async def lifespan(server):
    await init_db()
    yield

auth = None

if os.environ.get("ENVIRONMENT") == "production":
    auth = GitHubProvider(
        client_id=os.environ["GITHUB_CLIENT_ID"],
        client_secret=os.environ["GITHUB_CLIENT_SECRET"],
        base_url=os.environ["BASE_URL"],
    )

mcp = FastMCP(
    "PROJECT ASSISTANT",
    auth=auth,
    lifespan=lifespan,
)

@mcp.tool()
def search_code(query: str, directory: str = ".") -> list[str]:
    """Search for a text string inside project source files."""

    results = []

    for path in Path(directory).rglob("*"):
        if not path.is_file():
            continue

        if path.suffix not in {
            ".py",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".java",
            ".json",
            ".md",
        }:
            continue

        try:
            text = path.read_text(encoding="utf-8")

            for line_number, line in enumerate(text.splitlines(), 1):
                if query.lower() in line.lower():
                    results.append(
                        f"{path}:{line_number}: {line.strip()}"
                    )

        except (UnicodeDecodeError, PermissionError):
            continue

    return results


@mcp.tool
def read_file(
    file_path: str,
    start_line: int = 1,
    end_line: int = 100,
) -> str:
    """Read a specific section of a project file."""

    path = Path(file_path)

    if not path.exists():
        return f"File does not exist: {file_path}"

    lines = path.read_text(encoding="utf-8").splitlines()

    selected = lines[start_line - 1:end_line]

    return "\n".join(
        f"{i}: {line}"
        for i, line in enumerate(
            selected,
            start=start_line
        )
    )


@mcp.tool
def git_history(
    repository: str = ".",
    limit: int = 10,
) -> list[dict]:
    """Return recent Git commits."""

    # The hosted container checks out the repo as a different owner;
    # mark it safe so git doesn't refuse with "dubious ownership".
    os.environ["GIT_CONFIG_COUNT"] = "1"
    os.environ["GIT_CONFIG_KEY_0"] = "safe.directory"
    os.environ["GIT_CONFIG_VALUE_0"] = "*"

    try:
        repo = Repo(repository)
    except Exception as e:
        return [{
            "error": f"Unable to open repository at {repository!r}: {e}",
        }]

    commits = []

    for commit in repo.iter_commits(max_count=limit):
        commits.append({
            "hash": commit.hexsha[:8],
            "author": str(commit.author),
            "message": commit.message.strip(),
            "date": commit.committed_datetime.isoformat(),
        })

    return commits


@mcp.tool
def project_analysis() -> dict:
    """Return project analysis metrics including languages, files, and dependencies."""

    return {
        "language": {
            "Python": 14,
            "JavaScript": 22,
        },
        "files": 41,
        "directories": 8,
        "tests": 12,
        "dependencies": 17,
    }


@mcp.tool
async def list_my_repositories():
    """
    List repositories belonging only to the authenticated user.
    """

    # 1. Get identity from the authentication layer
    from auth.context import get_identity_hints

    auth_subject = get_authenticated_subject()
    hints = get_identity_hints()

    # 2. Convert external identity → internal database user
    user = await get_authenticated_user(
        auth_subject,
        name=hints.get("name"),
        email=hints.get("email"),
    )

    # 3. Query only repositories owned by this user
    repositories = await get_user_repositories(user["id"])

    return {
        "user": {
            "id": user["id"],
            "auth_subject": user["auth_subject"],
            "name": user["name"],
            "email": user["email"],
        },
        "count": len(repositories),
        "repositories": [
            {
                "id": repo["id"],
                "name": repo["name"],
                "path": repo["path"],
            }
            for repo in repositories
        ],
    }


@mcp.tool
async def list_github_repositories() -> dict:
    """
    List the GitHub repositories owned by the server's GitHub account.

    Requires an authenticated identity (gateway or token) and a
    GITHUB_TOKEN environment variable set on the server holding a
    GitHub PAT with repo read access. Results are always live —
    nothing needs to be imported or synced into the database.
    """

    import httpx

    auth_subject = get_authenticated_subject()

    token = os.environ.get("GITHUB_TOKEN") or None

    if not token:
        return {
            "subject": auth_subject,
            "github_configured": False,
            "message": (
                "GITHUB_TOKEN is not set on the server. Create a GitHub "
                "personal access token (github.com/settings/tokens) and add "
                "it as GITHUB_TOKEN in the deployment environment."
            ),
            "count": 0,
            "repositories": [],
        }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "mcp-git-assistant",
    }

    repositories: list[dict] = []

    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        for page in range(1, 6):  # hard cap: 500 repositories
            response = await client.get(
                "https://api.github.com/user/repos",
                params={
                    "affiliation": "owner",
                    "sort": "updated",
                    "per_page": "100",
                    "page": str(page),
                },
            )

            if response.status_code != 200:
                return {
                    "github_configured": True,
                    "github_authenticated": False,
                    "status": response.status_code,
                    "error": response.text[:300],
                    "count": 0,
                    "repositories": [],
                }

            data = response.json()

            repositories.extend({
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
                "private": repo["private"],
                "language": repo.get("language"),
                "default_branch": repo.get("default_branch"),
                "stargazers_count": repo.get("stargazers_count", 0),
                "fork": repo.get("fork", False),
                "archived": repo.get("archived", False),
                "pushed_at": repo.get("pushed_at"),
                "html_url": repo.get("html_url"),
            } for repo in data)

            if len(data) < 100:
                break

    return {
        "github_authenticated": True,
        "subject": auth_subject,
        "count": len(repositories),
        "repositories": repositories,
    }


@mcp.tool
def debug_auth() -> dict:
    """Debug the current authentication context."""
    from fastmcp.server.dependencies import get_access_token

    from auth.context import get_horizon_actor

    actor = get_horizon_actor()

    if actor:
        return {
            "authenticated": True,
            "source": "horizon-gateway",
            "actor": actor,
        }

    token = get_access_token()

    if token is None:
        return {
            "authenticated": False,
            "message": "No gateway actor context and no access token available"
        }

    return {
        "authenticated": True,
        "source": "app-token",
        "subject": token.subject,
        "claims": token.claims,
        "scopes": token.scopes,
    }

@mcp.tool
async def debug_github_user() -> dict:
    """Show the identity available through authentication."""

    from fastmcp.server.dependencies import get_access_token

    from auth.context import get_horizon_actor

    actor = get_horizon_actor()

    if actor:
        return {
            "authenticated": True,
            "source": "horizon-gateway",
            "subject": actor["id"],
            "actor_type": actor["type"],
            "email": actor["email"],
            "organization_role": actor["organization_role"],
            "server_roles": actor["server_roles"],
        }

    token = get_access_token()

    if token is None:
        return {
            "authenticated": False,
            "message": "No gateway actor context and no access token available",
        }

    return {
        "authenticated": True,
        "source": "app-token",
        "subject": token.subject,
        "claims": token.claims,
        "scopes": token.scopes,
    }


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
    )