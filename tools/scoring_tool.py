def calculate_scores(repo_data: dict) -> dict:
    """Calculate deterministic engineering maturity scores from repo signals."""
    scores = {
        "documentation": 0,
        "security": 0,
        "maintainability": 0,
        "devops": 0,
        "scalability": 0,
    }

    files = repo_data.get("files", [])
    readme = repo_data.get("readme", "")

    if readme and readme not in {"No README available.", "Error fetching README."}:
        scores["documentation"] += 7

    if any("docs/" in f.lower() or f.lower().endswith(".md") for f in files):
        scores["documentation"] += 3

    if any("Dockerfile" in f for f in files):
        scores["devops"] += 5

    if any(".github/workflows" in f for f in files):
        scores["devops"] += 5

    if any("test" in f.lower() or "spec" in f.lower() for f in files):
        scores["maintainability"] += 5

    if any(
        "eslint" in f.lower()
        or "prettier" in f.lower()
        or "ruff" in f.lower()
        or "flake8" in f.lower()
        or "black" in f.lower()
        for f in files
    ):
        scores["maintainability"] += 5

    if any(".env.example" in f for f in files):
        scores["security"] += 5

    if any(
        "security" in f.lower()
        or "auth" in f.lower()
        or "middleware" in f.lower()
        for f in files
    ):
        scores["security"] += 5

    if any("services" in f.lower() for f in files):
        scores["scalability"] += 5

    if any(
        "queue" in f.lower()
        or "worker" in f.lower()
        or "cache" in f.lower()
        or "packages/" in f
        for f in files
    ):
        scores["scalability"] += 5

    total = round(sum(scores.values()) / len(scores), 1)

    return {
        "category_scores": scores,
        "overall_score": total,
    }
