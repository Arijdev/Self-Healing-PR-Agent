import os
from agent import build_graph

def setup_mock_files():
    """Creates a mock Python file with an intentional bug for the agent to fix."""
    os.makedirs("src", exist_ok=True)
    mock_file_path = "src/math_utils.py"
    
    # Intentional bug: add function actually multiplies
    mock_code = """
def add(a, b):
    # This should add two numbers
    return a * b

def subtract(a, b):
    return a - b
"""
    with open(mock_file_path, "w", encoding="utf-8") as f:
        f.write(mock_code.strip())
        
    return [mock_file_path]

def main():
    print("Initializing Self-Healing Repo-Maintenance & PR Agent...")
    
    # 1. Setup mock environment
    target_files = setup_mock_files()
    print(f"Mock files created at: {target_files}")
    
    # 2. Define the initial state
    initial_state = {
        "task_description": "Fix the bug in the add function where it multiplies instead of adding. Then ensure there is 100% test coverage for src/math_utils.py.",
        "target_files": target_files,
        "generated_code": {},
        "test_files": {},
        "test_output": "",
        "test_status": False,
        "iteration_count": 0,
        "human_approved": False,
        "pr_url": None
    }
    
    # 3. Build and run the graph
    app = build_graph()
    
    print("\nStarting Agent Workflow...\n")
    
    try:
        final_state = app.invoke(initial_state)
        
        print("\n--- WORKFLOW COMPLETE ---")
        if final_state.get("pr_url"):
            print(f"Success! PR generated at: {final_state['pr_url']}")
        elif final_state.get("human_approved") is False:
            print("Workflow finished, but human approval was denied.")
        else:
            print("Workflow finished without generating a PR.")
            
    except Exception as e:
        print(f"Workflow failed: {e}")

if __name__ == "__main__":
    main()
