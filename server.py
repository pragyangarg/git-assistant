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

    repo = Repo(repository)

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
    auth_subject = get_authenticated_subject()

    # 2. Convert external identity → internal database user
    user = await get_authenticated_user(auth_subject)

    # 3. Query only repositories owned by this user
    repositories = await get_user_repositories(user["id"])

    return [
        {
            "id": repo["id"],
            "name": repo["name"],
            "path": repo["path"],
        }
        for repo in repositories
    ]


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
    )