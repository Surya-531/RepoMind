import os
import sys

import streamlit as st
import streamlit.components.v1 as components

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.analyzer_agent import analyze_repo
from agents.comparison_agent import compare_repositories
from tools.github_tool import get_repo_data


def render_mermaid_diagram(mermaid_code: str, height: int = 520) -> None:
    """Render a Mermaid diagram in Streamlit."""
    components.html(
        f"""
        <div class="mermaid">
        {mermaid_code}
        </div>
        <script type="module">
            import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
            mermaid.initialize({{
                startOnLoad: true,
                theme: "dark",
                flowchart: {{
                    curve: "basis",
                    nodeSpacing: 46,
                    rankSpacing: 64,
                    padding: 18
                }},
                themeVariables: {{
                    background: "#0e1117",
                    primaryColor: "#18202b",
                    primaryTextColor: "#f8fafc",
                    primaryBorderColor: "#38bdf8",
                    lineColor: "#94a3b8",
                    secondaryColor: "#111827",
                    tertiaryColor: "#020617",
                    clusterBkg: "#111827",
                    clusterBorder: "#334155",
                    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
                }}
            }});
        </script>
        """,
        height=height,
        scrolling=True,
    )


def render_report(report: str) -> None:
    """Render Markdown report and convert Mermaid code blocks into diagrams."""
    opening = "```mermaid"
    closing = "```"
    remaining = report

    while opening in remaining:
        before, after_opening = remaining.split(opening, 1)
        if before.strip():
            st.markdown(before)

        if closing not in after_opening:
            st.code(after_opening, language="mermaid")
            return

        mermaid_code, remaining = after_opening.split(closing, 1)
        mermaid_code = mermaid_code.strip().replace('\\"', '"')
        render_mermaid_diagram(mermaid_code)

        with st.expander("View Mermaid source"):
            st.code(mermaid_code, language="mermaid")

    if remaining.strip():
        st.markdown(remaining)


st.set_page_config(
    page_title="RepoMind",
    layout="wide",
)

st.title("RepoMind")
st.subheader("AI Software Architecture Intelligence Agent")

analyze_tab, compare_tab = st.tabs(["Analyze", "Compare"])

with analyze_tab:
    repo_url = st.text_input("Enter GitHub Repository URL")

    if st.button("Analyze Repository", type="primary"):
        if not repo_url.strip():
            st.warning("Please enter a GitHub repository URL.")
        else:
            with st.spinner("Analyzing repository..."):
                data = get_repo_data(repo_url)

                if "error" in data:
                    st.error(data["error"])
                else:
                    report = analyze_repo(data)
                    render_report(report)

with compare_tab:
    repo_a_url = st.text_input("Repository A URL")
    repo_b_url = st.text_input("Repository B URL")

    if st.button("Compare Repositories"):
        if not repo_a_url.strip() or not repo_b_url.strip():
            st.warning("Please enter both GitHub repository URLs.")
        else:
            with st.spinner("Comparing repositories..."):
                repo_a = get_repo_data(repo_a_url)
                repo_b = get_repo_data(repo_b_url)

                if "error" in repo_a:
                    st.error(f"Repository A: {repo_a['error']}")
                elif "error" in repo_b:
                    st.error(f"Repository B: {repo_b['error']}")
                else:
                    report = compare_repositories(repo_a, repo_b)
                    render_report(report)
