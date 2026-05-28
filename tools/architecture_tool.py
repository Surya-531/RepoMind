from utils.detector import detect_architecture, detect_missing_systems
from tools.diagram_tool import generate_mermaid_diagram


def build_architecture_profile(repo_data: dict) -> dict:
    """Build a compact architecture profile for agents and UI consumers."""
    files = repo_data.get("files", [])

    return {
        "architecture": detect_architecture(files),
        "missing_systems": detect_missing_systems(files),
        "diagram": generate_mermaid_diagram(files),
    }
