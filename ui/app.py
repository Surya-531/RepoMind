import os
import sys

import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.analyzer_agent import analyze_repo
from agents.comparison_agent import compare_repositories
from tools.github_tool import get_repo_data


st.set_page_config(
    page_title="RepoMind X",
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
                    st.markdown(report)

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
                    st.markdown(report)
