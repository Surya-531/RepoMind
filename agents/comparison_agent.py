from agents.analyzer_agent import analyze_repo


def compare_repositories(repo_a: dict, repo_b: dict) -> str:
    """Analyze two repositories and return a comparison-ready report."""
    report_a = analyze_repo(repo_a)
    report_b = analyze_repo(repo_b)

    return f"""
# Repository Comparison

## Repository A
{repo_a.get("repo_name", "Unknown repository")}

{report_a}

------------------------------------------------

## Repository B
{repo_b.get("repo_name", "Unknown repository")}

{report_b}

------------------------------------------------

# Final Verdict

Compare:
- architecture
- scalability
- maintainability
- production readiness
"""
