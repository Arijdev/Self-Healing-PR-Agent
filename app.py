import streamlit as st
import time
from agent import build_graph
from main import setup_mock_files
from config import TARGET_REPO_URL, GEMINI_API_KEY

st.set_page_config(page_title="Self-Healing PR Agent", layout="wide")

st.title("🤖 Autonomous Self-Healing PR Agent")
st.markdown("Read-Only Live Observability Dashboard")

if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY is not set. Please configure it in .env or st.secrets to run the agent.")
    st.stop()

if "workflow_finished" not in st.session_state:
    st.session_state.workflow_finished = False

def run_agent():
    # Setup mock
    target_files = setup_mock_files()
    initial_state = {
        "task_description": "Fix the bug in the add function where it multiplies instead of adding. Then ensure there is 100% test coverage.",
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
    
    status_placeholder = st.empty()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Test Execution Terminal")
        terminal_placeholder = st.empty()
    with col2:
        st.subheader("Healed Code Generation")
        diff_placeholder = st.empty()
        
    final_placeholder = st.empty()
    
    # Store the cumulative state to render diffs and terminal
    current_test_output = "Waiting for tests..."
    current_generated_code = {"status": "Waiting for generation..."}
    final_pr_url = None
    
    terminal_placeholder.code(current_test_output, language="bash")
    diff_placeholder.json(current_generated_code)
    
    # Stream events
    with status_placeholder.container():
        with st.status("Initializing Workflow Pipeline...", expanded=True) as status:
            for s in app.stream(initial_state, stream_mode="updates"):
                node_name = list(s.keys())[0]
                state_data = s[node_name]
                
                status.write(f"✅ Executed node: **`{node_name}`**")
                
                # Update UI components dynamically
                if "test_output" in state_data:
                    current_test_output = state_data["test_output"]
                    terminal_placeholder.code(current_test_output, language="bash")
                
                if "generated_code" in state_data:
                    current_generated_code = state_data["generated_code"]
                    diff_placeholder.json(current_generated_code)
                    
                if "pr_url" in state_data:
                    final_pr_url = state_data["pr_url"]
                
                # Small sleep to simulate observability in real-time
                time.sleep(1)
                
            status.update(label="Workflow Complete!", state="complete", expanded=False)
            
    # Final Artifact Card
    with final_placeholder.container():
        st.subheader("Final Artifact")
        if final_pr_url:
            st.success("🎉 Agent successfully healed the code and created a PR!")
            st.markdown(f"**Pull Request URL:** [{final_pr_url}]({final_pr_url})")
            if TARGET_REPO_URL:
                st.markdown(f"**Target Repository:** [{TARGET_REPO_URL}]({TARGET_REPO_URL})")
        else:
            st.info("Workflow completed without generating a PR. The agent might have reached max iterations or failed.")
            
    st.session_state.workflow_finished = True

if not st.session_state.workflow_finished:
    run_agent()
else:
    st.info("Workflow has already completed for this session. Refresh the page to run again.")
