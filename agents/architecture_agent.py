from tools.architecture_tool import build_architecture_profile
from tools.scoring_tool import calculate_scores


def analyze_architecture(repo_data: dict) -> dict:
    """Return deterministic architecture, maturity, and scoring signals."""
    profile = build_architecture_profile(repo_data)
    profile["score_data"] = calculate_scores(repo_data)
    return profile
