import base64
import logging
import re
import os
import requests

from config import README_CHAR_LIMIT, FILE_LIMIT, COMMIT_LIMIT, GITHUB_TOKEN

logger = logging.getLogger("repomind.github_tool")

BASE_URL = "https://api.github.com"


HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"
}

# Add auth token if provided (raises rate limit from 60 to 5000/hr)
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    logger.info("GitHub token loaded — using authenticated requests.")


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

    readme = fetch_readme(owner, repo)
    files = fetch_file_tree(owner, repo)
    commits = fetch_commits(owner, repo)
    meta = fetch_repo_meta(owner, repo)

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
