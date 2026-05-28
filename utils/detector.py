def detect_missing_systems(files: list[str]) -> list[str]:
    """Detect important engineering systems that are not visible in the repo."""
    issues = []

    if not any("Dockerfile" in f for f in files):
        issues.append("No Docker support detected")

    if not any(".github/workflows" in f for f in files):
        issues.append("No CI/CD pipeline detected")

    if not any("test" in f.lower() or "spec" in f.lower() for f in files):
        issues.append("No automated testing detected")

    if not any(".env.example" in f for f in files):
        issues.append("No environment template detected")

    if not any(
        "eslint" in f.lower()
        or "prettier" in f.lower()
        or "ruff" in f.lower()
        or "flake8" in f.lower()
        or "black" in f.lower()
        for f in files
    ):
        issues.append("No linting or formatting configuration detected")

    if not any(
        "monitor" in f.lower()
        or "sentry" in f.lower()
        or "logging" in f.lower()
        or "observability" in f.lower()
        for f in files
    ):
        issues.append("No monitoring/logging system detected")

    return issues


def detect_architecture(files: list[str]) -> str:
    """Infer a high-level architecture style from the repository file paths."""
    paths = " ".join(files)

    if "apps/" in paths and "packages/" in paths:
        return "Monorepo architecture"

    if "src/components" in paths:
        return "Component-driven frontend architecture"

    if "controllers" in paths and "models" in paths:
        return "MVC architecture"

    if "services" in paths and "routes" in paths:
        return "Layered backend architecture"

    if "microservice" in paths:
        return "Microservices architecture"

    return "General modular architecture"
