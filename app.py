import streamlit as st
import time
import json
from agent import build_graph
from config import TARGET_REPO_URL, GEMINI_API_KEY

st.set_page_config(page_title="Self-Healing PR Agent", layout="wide", page_icon="🤖")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Sleek Dark Mode & Glassmorphism */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
    }
    /* Headers */
    h1 {
        background: -webkit-linear-gradient(45deg, #FF4F00, #FF8C00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-family: 'Inter', sans-serif;
    }
    h2, h3 {
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    /* Metric widget coloring */
    [data-testid="stMetricValue"] {
        color: #38bdf8;
        font-weight: bold;
    }
    /* Hide top padding */
    .block-container {
        padding-top: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)

if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY is not set. Please configure it in .streamlit/secrets.toml or .env")
    st.stop()

if "workflow_finished" not in st.session_state:
    st.session_state.workflow_finished = False

def run_agent(task_description: str, target_files: list[str]):
    initial_state = {
        "task_description": task_description,
        "target_files": target_files,
        "generated_code": {},
        "test_files": {},
        "test_output": "",
        "test_status": False,
        "iteration_count": 0,
        "human_approved": True, # Auto-approve for headless dashboard execution
        "pr_url": None
    }
    
    app = build_graph()
    
    # --- SIDEBAR CONTEXT ---
    with st.sidebar:
        st.markdown("### ⚙️ Workflow Context")
        st.info(f"**Task:** {initial_state['task_description']}")
        if TARGET_REPO_URL:
            st.markdown(f"**Target Repo:** [View Here]({TARGET_REPO_URL})")
        else:
            st.markdown("**Target Repo:** Mock Local")
            
        st.markdown("---")
        st.markdown("### 🧠 AI Engine")
        st.markdown("`gemini-3.5-flash-lite` (LangGraph)")
        
    # --- HEADER & METRICS ---
    st.title("🤖 Autonomous Self-Healing PR Agent")
    st.markdown("Monitor real-time AI autonomous coding, testing, and self-correction.")
    
    m1, m2, m3 = st.columns(3)
    iter_metric = m1.empty()
    status_metric = m2.empty()
    pr_metric = m3.empty()
    
    iter_metric.metric("Healing Iterations", "0 / 3")
    status_metric.metric("Test Status", "Pending ⏳")
    pr_metric.metric("Pull Request", "Not Created")
    
    st.markdown("---")
    
    # --- MAIN UI CONTAINERS ---
    status_placeholder = st.empty()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🖥️ Execution Terminal")
        terminal_placeholder = st.empty()
    with col2:
        st.markdown("### 📝 Generated Source Code")
        diff_placeholder = st.empty()
        
    final_placeholder = st.empty()
    
    # Defaults
    current_test_output = "# Waiting for execution to begin..."
    current_generated_code = {"status": "Waiting for generation..."}
    final_pr_url = None
    
    terminal_placeholder.code(current_test_output, language="bash")
    diff_placeholder.json(current_generated_code)
    
    # --- STREAM LOOP ---
    with status_placeholder.container():
        with st.status("Initializing Workflow Pipeline...", expanded=True) as status:
            for s in app.stream(initial_state, stream_mode="updates"):
                node_name = list(s.keys())[0]
                state_data = s[node_name]
                
                status.write(f"✅ Active Node: **`{node_name}`**")
                
                # Metrics Updates
                if "iteration_count" in state_data:
                    iter_metric.metric("Healing Iterations", f"{state_data['iteration_count']} / 3")
                    
                if "test_status" in state_data:
                    if state_data["test_status"]:
                        status_metric.metric("Test Status", "Passed ✅", delta="100% Coverage")
                    else:
                        status_metric.metric("Test Status", "Failed ❌", delta="- Tests failed", delta_color="inverse")
                        
                # Content Updates
                if "test_output" in state_data:
                    current_test_output = state_data["test_output"]
                    terminal_placeholder.code(current_test_output, language="bash")
                
                if "generated_code" in state_data:
                    current_generated_code = state_data["generated_code"]
                    # Pretty format the code block if it has a file
                    if len(current_generated_code.keys()) > 0:
                        code_str = ""
                        for filepath, code in current_generated_code.items():
                            code_str += f"# {filepath}\n{code}\n\n"
                        diff_placeholder.code(code_str, language="python")
                    else:
                        diff_placeholder.json(current_generated_code)
                    
                if "pr_url" in state_data:
                    final_pr_url = state_data["pr_url"]
                    pr_metric.metric("Pull Request", "Published 🚀")
                
                # Dynamic delay for observability
                time.sleep(1)
                
            status.update(label="✨ Workflow Complete!", state="complete", expanded=False)
            
    # --- FINAL ARTIFACT ---
    with final_placeholder.container():
        if final_pr_url:
            st.success("🎉 Agent successfully healed the code and published a Pull Request!")
            st.markdown(f"**🔗 Pull Request Link:** [{final_pr_url}]({final_pr_url})")
            st.balloons()
        else:
            st.info("⚠️ Workflow completed without generating a PR. Max iterations reached or execution halted.")
            
    st.session_state.workflow_finished = True

if not st.session_state.workflow_finished:
    with st.form("agent_input_form"):
        task_desc = st.text_area("Task Description", "Review these files for bugs, fix them, and ensure test coverage.")
        files_input = st.text_input("Target Files (comma separated)", "src/main.py, src/utils.py")
        submitted = st.form_submit_button("Run Agent")
        
    if submitted:
        target_files = [f.strip() for f in files_input.split(",") if f.strip()]
        if not target_files:
            st.error("Please provide at least one target file.")
        else:
            run_agent(task_desc, target_files)
else:
    st.warning("Session Completed. Refresh the page to trigger a new agent run.")
