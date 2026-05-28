from utils.detector import (
    detect_architecture,
    detect_missing_systems
)

from tools.diagram_tool import generate_mermaid_diagram
from tools.architecture_tool import analyze_project_structure


def build_architecture_profile(repo_data: dict) -> dict:
    """
    Build a rich architecture intelligence profile
    for RepoMind analysis.
    """

    files = repo_data.get("files", [])

    structure = analyze_project_structure(files)

    return {
        "architecture": detect_architecture(files),

        "missing_systems": detect_missing_systems(files),

        "diagram": generate_mermaid_diagram(files),

        "structure": structure,

        "frontend_detected": structure["frontend"],

        "backend_detected": structure["backend"],

        "database_detected": structure["database"],

        "api_detected": structure["api"],

        "testing_detected": structure["testing"],

        "docker_detected": structure["docker"],

        "ci_cd_detected": structure["ci_cd"],

        "microservices_detected": structure["microservices"],

        "monorepo_detected": structure["monorepo"],
    }