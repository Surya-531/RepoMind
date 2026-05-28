import sys
import logging

from tools.github_tool import get_repo_data
from agents.analyzer_agent import analyze_repo
from utils.parser import extract_score

logger = logging.getLogger("repomind.main")


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║          🧠  RepoMind — AI Repo Analyzer                 ║
║               Powered by AI + LangChain                  ║
╚══════════════════════════════════════════════════════════╝
""")


def run(repo_url: str = None):
    print_banner()

    if not repo_url:
        repo_url = input("🔗 Enter GitHub Repo URL: ").strip()

    if not repo_url:
        print("❌ No URL provided. Exiting.")
        sys.exit(1)

    print(f"\n🔍 Fetching repository data for: {repo_url}\n")
    repo_data = get_repo_data(repo_url)

    if "error" in repo_data:
        print(f"❌ Error: {repo_data['error']}")
        sys.exit(1)

    print(f"✅ Data fetched:")
    print(f"   • README    : {len(repo_data.get('readme', ''))} chars")
    print(f"   • Files     : {len(repo_data.get('files', []))} found")
    print(f"   • Commits   : {len(repo_data.get('commits', []))} recent")
    print(f"   • Language  : {repo_data.get('meta', {}).get('language', 'Unknown')}")
    print(f"   • Stars     : {repo_data.get('meta', {}).get('stars', 0)}")

    print("\n🧠 Running AI analysis with Grok...\n")

    try:
        report = analyze_repo(repo_data)
    except RuntimeError as e:
        print(f"❌ Analysis error: {e}")
        sys.exit(1)

    score = extract_score(report)

    print("=" * 60)
    print(report)
    print("=" * 60)

    if score != "N/A":
        print(f"\n📊 Production Readiness Score extracted: {score}/10")

    print("\n✅ RepoMind analysis complete.\n")


if __name__ == "__main__":
    # Optionally accept repo URL as CLI argument
    url = sys.argv[1] if len(sys.argv) > 1 else None
    run(url)
