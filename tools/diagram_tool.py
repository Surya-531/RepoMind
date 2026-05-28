from tools.architecture_tool import analyze_project_structure


def _normalized(files: list[str]) -> list[str]:
    return [file.replace("\\", "/").lower() for file in files]


def _has_any(files: list[str], signals: list[str]) -> bool:
    return any(any(signal in file for signal in signals) for file in files)


def _append_node(lines: list[str], node_id: str, label: str) -> None:
    lines.append(f'        {node_id}["{label}"]')


def _append_edge(lines: list[str], source: str, target: str, label: str | None = None) -> None:
    if label:
        lines.append(f'    {source} -->|"{label}"| {target}')
    else:
        lines.append(f"    {source} --> {target}")


def _append_class(lines: list[str], nodes: list[str], class_name: str) -> None:
    if nodes:
        lines.append(f"    class {','.join(nodes)} {class_name}")


def _append_styles(lines: list[str]) -> None:
    lines.extend(
        [
            "    classDef entry fill:#0f766e,stroke:#5eead4,color:#ecfeff,stroke-width:2px",
            "    classDef ui fill:#1d4ed8,stroke:#93c5fd,color:#eff6ff,stroke-width:2px",
            "    classDef app fill:#7c3aed,stroke:#c4b5fd,color:#faf5ff,stroke-width:2px",
            "    classDef data fill:#b45309,stroke:#fcd34d,color:#fffbeb,stroke-width:2px",
            "    classDef platform fill:#334155,stroke:#94a3b8,color:#f8fafc,stroke-width:2px",
            "    classDef external fill:#be123c,stroke:#fda4af,color:#fff1f2,stroke-width:2px",
            "    class Repo entry",
        ]
    )


def _append_repo_mind_diagram(lines: list[str], files: list[str]) -> bool:
    has_ui = _has_any(files, ["ui/", "streamlit"])
    has_agents = _has_any(files, ["agents/"])
    has_tools = _has_any(files, ["tools/"])
    has_utils = _has_any(files, ["utils/"])
    has_config = _has_any(files, ["config.py", ".env", "requirements.txt"])
    has_github_tool = _has_any(files, ["github_tool"])
    has_llm_agent = _has_any(files, ["analyzer_agent", "comparison_agent", "langchain", "openai"])

    if not (has_ui and has_agents and has_tools):
        return False

    lines.extend(
        [
            '    User(("User"))',
            '    subgraph Interface["Interactive Interface"]',
            '        UI["Streamlit App"]',
            "    end",
            '    subgraph Intelligence["Agent Orchestration"]',
            '        Analyzer["Repository Analyzer"]',
            '        Comparator["Repository Comparator"]',
            "    end",
            '    subgraph Capabilities["Repository Intelligence Tools"]',
            '        GitHubTool["GitHub Data Fetcher"]',
            '        DiagramTool["Architecture Diagram Builder"]',
            '        ScoringTool["Readiness Scoring"]',
            "    end",
        ]
    )

    if has_utils:
        lines.extend(
            [
                '    subgraph Support["Parsing and Detection"]',
                '        Detector["Architecture Detector"]',
                '        Parser["Prompt Context Builder"]',
                "    end",
            ]
        )

    if has_config:
        lines.extend(
            [
                '    subgraph Runtime["Runtime Configuration"]',
                '        Config["Model, API, and Env Config"]',
                "    end",
            ]
        )

    lines.extend(
        [
            '    subgraph External["External Services"]',
            '        GitHubAPI[("GitHub API")]',
            '        LLM[("LLM Provider")]',
            "    end",
            '    Report["Structured Engineering Report"]',
            '    Diagram["Rendered Mermaid Diagram"]',
        ]
    )

    _append_edge(lines, "User", "UI", "submits repository URL")
    _append_edge(lines, "Repo", "UI", "contains")
    _append_edge(lines, "UI", "GitHubTool", "requests metadata")

    if has_github_tool:
        _append_edge(lines, "GitHubTool", "GitHubAPI", "fetches README, tree, commits")

    _append_edge(lines, "UI", "Analyzer", "analyze")
    _append_edge(lines, "UI", "Comparator", "compare")
    _append_edge(lines, "Analyzer", "DiagramTool", "builds")
    _append_edge(lines, "Analyzer", "ScoringTool", "scores")

    if has_utils:
        _append_edge(lines, "Analyzer", "Detector", "detects architecture")
        _append_edge(lines, "Analyzer", "Parser", "builds prompt")

    if has_config:
        _append_edge(lines, "Analyzer", "Config", "uses")
        _append_edge(lines, "Comparator", "Config", "uses")

    if has_llm_agent:
        _append_edge(lines, "Analyzer", "LLM", "generates analysis")
        _append_edge(lines, "Comparator", "LLM", "generates comparison")

    _append_edge(lines, "DiagramTool", "Diagram", "outputs")
    _append_edge(lines, "LLM", "Report", "returns")
    _append_edge(lines, "Report", "UI", "displays")
    _append_edge(lines, "Diagram", "UI", "renders")

    _append_class(lines, ["User", "Repo"], "entry")
    _append_class(lines, ["UI", "Report", "Diagram"], "ui")
    _append_class(
        lines,
        ["Analyzer", "Comparator", "GitHubTool", "DiagramTool", "ScoringTool"],
        "app",
    )
    if has_utils:
        _append_class(lines, ["Detector", "Parser"], "platform")
    if has_config:
        _append_class(lines, ["Config"], "platform")
    _append_class(lines, ["GitHubAPI", "LLM"], "external")
    return True


def generate_mermaid_diagram(files: list[str]) -> str:
    """
    Generate a readable layered Mermaid architecture diagram from a repository tree.
    """

    normalized_files = _normalized(files)
    structure = analyze_project_structure(files)

    has_pages = _has_any(normalized_files, ["pages/", "app/", "views/", "screens/"])
    has_components = _has_any(normalized_files, ["components/", "ui/"])
    has_state = _has_any(
        normalized_files,
        ["hooks/", "context/", "store/", "redux", "zustand", "provider"],
    )
    has_assets = _has_any(normalized_files, ["assets/", "public/", "static/", "images/"])
    has_styles = _has_any(
        normalized_files,
        ["styles/", ".css", ".scss", "tailwind.config", "postcss.config"],
    )
    has_config = _has_any(
        normalized_files,
        [
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "vite.config",
            "next.config",
            "tsconfig",
            ".env",
        ],
    )
    has_services = _has_any(normalized_files, ["services/", "lib/", "utils/", "tools/"])
    has_routes = _has_any(normalized_files, ["routes/", "controllers/", "api/"])
    has_middleware = _has_any(normalized_files, ["middleware/"])

    lines = [
        "```mermaid",
        "graph LR",
        '    Repo["Repository Root"]',
    ]

    if _append_repo_mind_diagram(lines, normalized_files):
        _append_styles(lines)
        lines.append("```")
        return "\n".join(lines)

    client_nodes: list[str] = []
    backend_nodes: list[str] = []
    platform_nodes: list[str] = []

    if structure["frontend"]:
        lines.append('    subgraph Client["Client / Presentation Layer"]')
        _append_node(lines, "Frontend", "Frontend App")
        client_nodes.append("Frontend")

        if has_pages:
            _append_node(lines, "Pages", "Pages / Routes")
            client_nodes.append("Pages")

        if has_components:
            _append_node(lines, "Components", "Reusable UI Components")
            client_nodes.append("Components")

        if has_state:
            _append_node(lines, "State", "State, Hooks, Context")
            client_nodes.append("State")

        if has_styles:
            _append_node(lines, "Styles", "Styling System")
            client_nodes.append("Styles")

        if has_assets:
            _append_node(lines, "Assets", "Static Assets")
            client_nodes.append("Assets")

        lines.append("    end")

    if structure["api"] or structure["backend"] or has_services:
        lines.append('    subgraph Application["Application / Service Layer"]')

        if structure["api"] or has_routes:
            _append_node(lines, "API", "API Routes / Controllers")
            backend_nodes.append("API")

        if structure["backend"] or has_services:
            _append_node(lines, "Services", "Business Logic / Services")
            backend_nodes.append("Services")

        if has_middleware:
            _append_node(lines, "Middleware", "Middleware")
            backend_nodes.append("Middleware")

        lines.append("    end")

    if structure["database"]:
        lines.append('    subgraph Data["Data Layer"]')
        lines.append('        DB[("Database / ORM Schema")]')
        lines.append("    end")

    if structure["testing"] or structure["docker"] or structure["ci_cd"] or has_config:
        lines.append('    subgraph Platform["Quality, Config, and Delivery"]')

        if structure["testing"]:
            _append_node(lines, "Tests", "Automated Tests")
            platform_nodes.append("Tests")

        if has_config:
            _append_node(lines, "Config", "Runtime / Build Config")
            platform_nodes.append("Config")

        if structure["docker"]:
            _append_node(lines, "Docker", "Docker Packaging")
            platform_nodes.append("Docker")

        if structure["ci_cd"]:
            _append_node(lines, "CI", "CI/CD Workflow")
            platform_nodes.append("CI")

        lines.append("    end")

    if not client_nodes and not backend_nodes and not platform_nodes and not structure["database"]:
        lines.extend(
            [
                '    Source["Source Code"]',
                '    Config["Configuration"]',
                '    Runtime["Runtime"]',
                "    Repo --> Source",
                "    Repo --> Config",
                "    Source --> Runtime",
            ]
        )
        _append_styles(lines)
        lines.append("```")
        return "\n".join(lines)

    if client_nodes:
        _append_edge(lines, "Repo", "Frontend", "contains")
        if "Pages" in client_nodes:
            _append_edge(lines, "Frontend", "Pages", "renders")
        if "Components" in client_nodes:
            target = "Pages" if "Pages" in client_nodes else "Frontend"
            _append_edge(lines, target, "Components", "composes")
        if "State" in client_nodes:
            target = "Components" if "Components" in client_nodes else "Frontend"
            _append_edge(lines, target, "State", "uses")
        if "Styles" in client_nodes:
            _append_edge(lines, "Frontend", "Styles", "styles")
        if "Assets" in client_nodes:
            _append_edge(lines, "Frontend", "Assets", "loads")

    if backend_nodes:
        entry_node = "API" if "API" in backend_nodes else "Services"
        _append_edge(lines, "Repo", entry_node, "contains")

        if "API" in backend_nodes and "Services" in backend_nodes:
            _append_edge(lines, "API", "Services", "delegates")

        if "Middleware" in backend_nodes and "API" in backend_nodes:
            _append_edge(lines, "Middleware", "API", "guards")

        if client_nodes:
            client_edge_source = "State" if "State" in client_nodes else client_nodes[-1]
            _append_edge(lines, client_edge_source, entry_node, "requests")

    if structure["database"]:
        data_source = "Services" if "Services" in backend_nodes else "API"
        if data_source in backend_nodes:
            _append_edge(lines, data_source, "DB", "reads/writes")
        else:
            _append_edge(lines, "Repo", "DB", "defines")

    for node in platform_nodes:
        _append_edge(lines, "Repo", node, "supports")

    if "Tests" in platform_nodes:
        test_target = "Services" if "Services" in backend_nodes else "Frontend"
        if test_target in backend_nodes or test_target in client_nodes:
            _append_edge(lines, "Tests", test_target, "validates")

    if "CI" in platform_nodes:
        deploy_target = "Docker" if "Docker" in platform_nodes else "Tests"
        if deploy_target in platform_nodes:
            _append_edge(lines, "CI", deploy_target, "runs")

    _append_class(lines, client_nodes, "ui")
    _append_class(lines, backend_nodes, "app")
    if structure["database"]:
        _append_class(lines, ["DB"], "data")
    _append_class(lines, platform_nodes, "platform")
    _append_styles(lines)
    lines.append("```")
    return "\n".join(lines)
