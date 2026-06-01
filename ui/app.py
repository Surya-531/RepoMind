import os
import sys

import streamlit as st
import streamlit.components.v1 as components

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.analyzer_agent import analyze_repo
from agents.comparison_agent import compare_repositories
from agents.qa_agent import answer_question
from tools.github_tool import get_repo_data
from tools.vector_store import build_vector_store


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

if "repo_data" not in st.session_state:
    st.session_state.repo_data = None
if "analysis_report" not in st.session_state:
    st.session_state.analysis_report = ""
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "qa_answer" not in st.session_state:
    st.session_state.qa_answer = ""

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
                    st.session_state.repo_data = data
                    st.session_state.analysis_report = report
                    st.session_state.qa_answer = ""

                    try:
                        st.session_state.vectorstore = build_vector_store(data, report)
                    except Exception as e:
                        st.session_state.vectorstore = None
                        st.warning(f"Analysis completed, but RepoMind Q&A could not be prepared: {e}")

    if st.session_state.analysis_report:
        render_report(st.session_state.analysis_report)

    st.divider()
    st.subheader("💬 Ask RepoMind")

    st.markdown(
        """
Example queries:

- How is the API structured?
- What frameworks are used?
- How does deployment work?
- What are the biggest scalability issues?
- Which files handle authentication?
- How would you improve this project?
"""
    )

    question = st.text_input(
        "Ask anything about this repository",
        placeholder="How does authentication work?",
    )

    ask_disabled = st.session_state.vectorstore is None
    if ask_disabled:
        st.info("Analyze a repository first to enable repository Q&A.")

    if st.button("Ask", disabled=ask_disabled):
        if not question.strip():
            st.warning("Please enter a question about the analyzed repository.")
        else:
            with st.spinner("Searching repository knowledge and drafting an answer..."):
                try:
                    st.session_state.qa_answer = answer_question(
                        st.session_state.vectorstore,
                        question,
                    )
                except Exception as e:
                    st.session_state.qa_answer = ""
                    st.error(f"Could not answer the question: {e}")

    if st.session_state.qa_answer:
        st.markdown(st.session_state.qa_answer)

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
