import re
import logging

logger = logging.getLogger("repomind.parser")


def format_file_list(files: list[str]) -> str:
    """Format file list into a readable string."""
    if not files:
        return "No files available."
    return "\n".join(f"  - {f}" for f in files)


def format_commits(commits: list[str]) -> str:
    """Format commit messages into a readable string."""
    if not commits:
        return "No commits available."
    return "\n".join(f"  [{i+1}] {msg}" for i, msg in enumerate(commits))


def format_meta(meta: dict) -> str:
    """Format repo metadata into a readable string."""
    if not meta:
        return "No metadata available."
    lines = []
    if meta.get("description"):
        lines.append(f"  Description : {meta['description']}")
    lines.append(f"  Language    : {meta.get('language', 'Unknown')}")
    lines.append(f"  Stars       : {meta.get('stars', 0)}")
    lines.append(f"  Forks       : {meta.get('forks', 0)}")
    lines.append(f"  Open Issues : {meta.get('open_issues', 0)}")
    lines.append(f"  License     : {meta.get('license', 'None')}")
    if meta.get("topics"):
        lines.append(f"  Topics      : {', '.join(meta['topics'])}")
    return "\n".join(lines)


def extract_score(report_text: str) -> str:
    """Try to extract the numeric score from the report."""
    match = re.search(r"(?:score|readiness)[^\d]{0,30}(\d+(?:\.\d+)?)\s*/\s*10", report_text, re.IGNORECASE)
    if match:
        return match.group(1)
    return "N/A"


def build_prompt_context(repo_data: dict) -> dict:
    """Prepare formatted strings for use in the LLM prompt."""
    return {
        "owner_repo": f"{repo_data.get('owner', '?')}/{repo_data.get('repo_name', repo_data.get('repo', '?'))}",
        "readme": repo_data.get("readme", "No README."),
        "files": format_file_list(repo_data.get("files", [])),
        "commits": format_commits(repo_data.get("commits", [])),
        "meta": format_meta(repo_data.get("meta", {})),
    }
