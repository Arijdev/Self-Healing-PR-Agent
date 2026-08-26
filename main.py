import os
from agent import build_graph

import argparse
import sys
from agent import build_graph

def main():
    parser = argparse.ArgumentParser(description="Self-Healing PR Agent")
    parser.add_argument("--files", type=str, required=True, help="Comma-separated list of target files")
    parser.add_argument("--task", type=str, required=True, help="Task description")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve and create PR")
    args = parser.parse_args()

    print("Initializing Self-Healing Repo-Maintenance & PR Agent...")
    
    target_files = [f.strip() for f in args.files.split(",") if f.strip()]
    if not target_files:
        print("Error: No valid target files provided.")
        sys.exit(1)
        
    print(f"Target files: {target_files}")
    print(f"Task: {args.task}")
    
    initial_state = {
        "task_description": args.task,
        "target_files": target_files,
        "generated_code": {},
        "test_files": {},
        "test_output": "",
        "test_status": False,
        "iteration_count": 0,
        "human_approved": args.auto_approve,
        "pr_url": None
    }
    
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
