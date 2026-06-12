import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config import BASE_URL, MODEL_NAME, OPENROUTER_API_KEY
from tools.diagram_tool import generate_mermaid_diagram
from tools.scoring_tool import calculate_scores
from utils.detector import detect_architecture, detect_missing_systems
from utils.parser import build_prompt_context

logger = logging.getLogger("repomind.analyzer_agent")

SYSTEM_PROMPT = """You are a senior software engineer and technical architect with 15+ years of experience.

Your task is to perform a deep technical analysis of a GitHub repository based on provided data.

Produce a STRUCTURED ENGINEERING REPORT with EXACTLY these sections:

REPOMIND ANALYSIS REPORT

1. PROJECT SUMMARY
   Describe the purpose, goals, and scope of the project in 3-5 sentences.

2. TECH STACK
   List all detected languages, frameworks, libraries, tools, databases, CI/CD, and infrastructure.
   Format: Category -> Technology

3. CODE QUALITY OBSERVATIONS
   Analyze code structure, naming conventions, documentation quality, test coverage signals,
   modularity, and design patterns. Be specific.

4. RISKS / ISSUES
   List technical risks, security concerns, dependency issues, missing practices, or red flags.
   Format as numbered list with severity: [HIGH] / [MEDIUM] / [LOW]

5. IMPROVEMENT SUGGESTIONS
   Provide 5-7 concrete, actionable recommendations a senior engineer would make.
   Prioritize by impact.

6. PRODUCTION READINESS SCORE
   Give a score from 0-10 with a one-line justification.
   Format: Score: X/10 - <reason>

   Scoring Guide:
   0-3 : Prototype / incomplete
   4-5 : Development-stage
   6-7 : Approaching production
   8-9 : Production-ready with minor gaps
   10  : Fully hardened, enterprise-grade

7. ARCHITECTURE ANALYSIS
   Detect architectural style and engineering maturity.

8. MISSING ENGINEERING SYSTEMS
   Identify critical missing systems:
   - tests
   - Docker
   - CI/CD
   - monitoring
   - linting
   - validation

9. ARCHITECTURE DIAGRAM
   Copy the generated Mermaid diagram exactly as provided. Do not summarize,
   simplify, rewrite, escape quotes, add backslashes, or replace it with a
   shorter diagram.

10. CATEGORY SCORES
   Analyze:
   - documentation
   - security
   - maintainability
   - scalability
   - devops

Be precise, technical, and critical. Do not praise without reason. Do not pad with filler text.
"""

HUMAN_PROMPT = """Analyze this GitHub repository: {owner_repo}

-- REPOSITORY METADATA --
{meta}

-- README (truncated to 3000 chars) --
{readme}

-- FILE TREE (up to 50 files) --
{files}

-- RECENT COMMITS (last 5) --
{commits}

-- DETECTED ARCHITECTURE --
{architecture}

-- MISSING SYSTEMS --
{missing_systems}

-- SCORE DATA --
{score_data}

-- GENERATED DIAGRAM --
{diagram}

Generate the full engineering report now.
"""


def create_llm() -> ChatOpenAI:
    """Initialize the LLM with API settings."""
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Add it in your Render environment variables.")

    logger.info(f"Initializing LLM: model={MODEL_NAME}, base_url={BASE_URL}")
    return ChatOpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=BASE_URL,
        model=MODEL_NAME,
        temperature=0.3,
        default_headers={
            "HTTP-Referer": "http://localhost",
            "X-Title": "RepoMind",
        },
    )


def analyze_repo(repo_data: dict) -> str:
    """
    Run the analysis chain on the fetched repo data.
    Returns the formatted report as a string.
    """
    llm = create_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", HUMAN_PROMPT),
        ]
    )

    chain = prompt | llm | StrOutputParser()

    files = repo_data.get("files", [])
    missing_systems = detect_missing_systems(files)
    architecture = detect_architecture(files)
    score_data = calculate_scores(repo_data)
    diagram = generate_mermaid_diagram(files)

    context = build_prompt_context(repo_data)
    context["missing_systems"] = "\n".join(f"- {x}" for x in missing_systems) or "- None detected"
    context["architecture"] = architecture
    context["score_data"] = score_data
    context["diagram"] = diagram
    logger.info(f"Sending analysis request for {context['owner_repo']}")

    try:
        report = chain.invoke(context)
        logger.info("Analysis complete.")
        return report
    except Exception as e:
        logger.error(f"LLM error: {e}")
        raise RuntimeError(f"Analysis failed: {e}") from e
