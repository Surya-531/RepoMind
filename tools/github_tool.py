import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import re
from urllib.parse import quote

import requests

from config import (
    COMMIT_LIMIT,
    CONTENT_CHAR_LIMIT,
    CONTENT_FILE_LIMIT,
    FILE_LIMIT,
    GITHUB_TOKEN,
    README_CHAR_LIMIT,
)

logger = logging.getLogger("repomind.github_tool")

BASE_URL = "https://api.github.com"


HEADERS = {
    "Accept": "application/vnd.github+json",
}

# Add auth token if provided (raises rate limit from 60 to 5000/hr)
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    logger.info("GitHub token loaded — using authenticated requests.")

CONFIG_FILE_NAMES = {
    ".env.example",
    ".gitlab-ci.yml",
    "Dockerfile",
    "docker-compose.yml",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements.txt",
    "pyproject.toml",
    "Pipfile",
    "poetry.lock",
    "pom.xml",
    "build.gradle",
    "settings.gradle",
    "go.mod",
    "Cargo.toml",
}

SOURCE_EXTENSIONS = (
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".rb",
    ".php",
    ".cs",
    ".rs",
)

IMPORTANT_PATH_HINTS = (
    "auth",
    "login",
    "jwt",
    "session",
    "security",
    "middleware",
    "user",
    "account",
    "config",
    ".github/workflows",
)


def parse_repo_url(repo_url: str) -> tuple[str, str]:
    """Extract owner and repo name from a GitHub URL."""
    repo_url = repo_url.strip().rstrip("/")

    # Match https://github.com/owner/repo or git@github.com:owner/repo
    match = re.search(r"github\.com[:/]([^/]+)/([^/\s.]+?)(?:\.git)?$", repo_url)
    if not match:
        raise ValueError(
            f"Invalid GitHub URL: '{repo_url}'. "
            "Expected format: https://github.com/owner/repo"
        )

    owner, repo = match.group(1), match.group(2)
    logger.info(f"Parsed repo: {owner}/{repo}")
    return owner, repo


def fetch_readme(owner: str, repo: str) -> str:
    """Fetch and decode the README file."""
    url = f"{BASE_URL}/repos/{owner}/{repo}/readme"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            content = res.json().get("content", "")
            decoded = base64.b64decode(content).decode("utf-8", errors="replace")
            logger.info(f"README fetched ({len(decoded)} chars)")
            return decoded[:README_CHAR_LIMIT]
        else:
            logger.warning(f"README not found (HTTP {res.status_code})")
            return "No README available."
    except Exception as e:
        logger.error(f"Error fetching README: {e}")
        return "Error fetching README."


def fetch_file_tree(owner: str, repo: str) -> list[str]:
    """Fetch the repository file tree."""
    url = f"{BASE_URL}/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            tree = res.json().get("tree", [])
            files = [
                item["path"]
                for item in tree
                if item.get("type") == "blob"
            ][:FILE_LIMIT]
            logger.info(f"File tree fetched: {len(files)} files")
            return files
        else:
            logger.warning(f"File tree not found (HTTP {res.status_code})")
            return []
    except Exception as e:
        logger.error(f"Error fetching file tree: {e}")
        return []


def fetch_commits(owner: str, repo: str) -> list[str]:
    """Fetch the most recent commit messages."""
    url = f"{BASE_URL}/repos/{owner}/{repo}/commits?per_page={COMMIT_LIMIT}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            commits = res.json()
            messages = [
                c.get("commit", {}).get("message", "").split("\n")[0]
                for c in commits
                if c.get("commit")
            ]
            logger.info(f"Commits fetched: {len(messages)}")
            return messages
        else:
            logger.warning(f"Commits not found (HTTP {res.status_code})")
            return []
    except Exception as e:
        logger.error(f"Error fetching commits: {e}")
        return []


def should_fetch_file(path: str) -> bool:
    """Choose high-signal files for repository Q&A."""
    normalized = path.replace("\\", "/")
    name = normalized.rsplit("/", 1)[-1]
    lower_path = normalized.lower()

    if normalized in CONFIG_FILE_NAMES or name in CONFIG_FILE_NAMES:
        return True

    if lower_path.startswith(".github/workflows/"):
        return True

    if any(hint in lower_path for hint in IMPORTANT_PATH_HINTS):
        return lower_path.endswith(SOURCE_EXTENSIONS) or "." in name

    return lower_path.endswith(SOURCE_EXTENSIONS) and (
        normalized.count("/") <= 2
        or name.lower() in {"app.py", "main.py", "server.js", "index.js"}
    )


def fetch_file_content(owner: str, repo: str, path: str) -> str:
    """Fetch and decode a single text file from the repository."""
    encoded_path = quote(path, safe="/")
    url = f"{BASE_URL}/repos/{owner}/{repo}/contents/{encoded_path}"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            logger.warning(f"Could not fetch {path} (HTTP {res.status_code})")
            return ""

        payload = res.json()
        if payload.get("encoding") != "base64" or "content" not in payload:
            return ""

        decoded = base64.b64decode(payload["content"]).decode("utf-8", errors="replace")
        return decoded[:CONTENT_CHAR_LIMIT]
    except Exception as e:
        logger.error(f"Error fetching file content for {path}: {e}")
        return ""


def fetch_selected_file_contents(owner: str, repo: str, files: list[str]) -> list[dict]:
    """Fetch selected config/source files to improve repository Q&A accuracy."""
    selected = [path for path in files if should_fetch_file(path)]
    selected = selected[:CONTENT_FILE_LIMIT]
    file_contents = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_path = {
            executor.submit(fetch_file_content, owner, repo, path): path
            for path in selected
        }

        for future in as_completed(future_to_path):
            path = future_to_path[future]
            content = future.result()
            if content.strip():
                file_contents.append(
                    {
                        "path": path,
                        "content": content,
                    }
                )

    logger.info(f"Fetched {len(file_contents)} file contents for Q&A")
    return file_contents


def fetch_repo_meta(owner: str, repo: str) -> dict:
    """Fetch basic repo metadata (stars, forks, language, etc.)."""
    url = f"{BASE_URL}/repos/{owner}/{repo}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return {
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "language": data.get("language", "Unknown"),
                "open_issues": data.get("open_issues_count", 0),
                "description": data.get("description", ""),
                "topics": data.get("topics", []),
                "license": (data.get("license") or {}).get("name", "None"),
                "default_branch": data.get("default_branch", "main"),
            }
        return {}
    except Exception as e:
        logger.error(f"Error fetching repo meta: {e}")
        return {}


def get_repo_data(repo_url: str) -> dict:
    """
    Main entry point. Given a GitHub repo URL, returns a dict with:
    - readme, files, commits, meta, owner, repo
    """
    try:
        owner, repo = parse_repo_url(repo_url)
    except ValueError as e:
        return {"error": str(e)}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            "readme": executor.submit(fetch_readme, owner, repo),
            "files": executor.submit(fetch_file_tree, owner, repo),
            "commits": executor.submit(fetch_commits, owner, repo),
            "meta": executor.submit(fetch_repo_meta, owner, repo),
        }
        readme = futures["readme"].result()
        files = futures["files"].result()
        commits = futures["commits"].result()
        meta = futures["meta"].result()

    file_contents = fetch_selected_file_contents(owner, repo, files)

    # Check if the repo actually exists / is accessible
    if not files and not commits and readme == "No README available.":
        return {
            "error": (
                f"Could not access repository '{owner}/{repo}'. "
                "It may be private, empty, or does not exist."
            )
        }

    return {
        "repo_name": repo,
        "repo": repo,
        "owner": owner,
        "readme": readme[:5000],
        "files": files,
        "file_contents": file_contents,
        "commits": commits,
        "meta": meta,
        "file_count": len(files),

        # intelligent detection
        "has_docker": any("Dockerfile" in f for f in files),
        "has_tests": any(
            "test" in f.lower() or "spec" in f.lower()
            for f in files
        ),
        "has_ci_cd": any(
            ".github/workflows" in f
            for f in files
        ),
        "has_env_example": any(
            ".env.example" in f
            for f in files
        ),
        "has_linter": any(
            "eslint" in f.lower()
            or "prettier" in f.lower()
            or "ruff" in f.lower()
            or "flake8" in f.lower()
            or "black" in f.lower()
            for f in files
        ),
    }
