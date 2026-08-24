from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
import re

from state import AgentState
from tools import read_files, write_files, run_pytest, create_git_pr
from config import GEMINI_API_KEY

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", google_api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def extract_json(content: str) -> dict:
    """Helper to parse JSON from LLM output, handling markdown blocks."""
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:-3].strip()
    elif content.startswith("```"):
        content = content[3:-3].strip()
    return json.loads(content)

def planner_and_coder(state: AgentState):
    print("--- PLANNER & CODER ---")
    files_content = read_files(state["target_files"])
    prompt = f"""
    You are an expert Python architect.
    Task: {state['task_description']}
    
    Current File Contents:
    {json.dumps(files_content, indent=2)}
    
    Please provide the complete, updated Python code for the target files.
    Format your response as a valid JSON object mapping file paths to their new content.
    Example: {{"math_utils.py": "def add(a, b):\n    return a + b\n"}}
    Do not output markdown block formatting around the JSON. Ensure it is strict JSON.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        generated_code = extract_json(response.content)
        # Write files to disk
        write_files(generated_code)
        return {"generated_code": generated_code}
    except Exception as e:
        print(f"Error parsing code generation: {e}")
        print(f"Raw output: {response.content}")
        return {"generated_code": files_content}

def test_generator(state: AgentState):
    print("--- TEST GENERATOR ---")
    prompt = f"""
    You are an expert QA Engineer.
    Task: Write comprehensive pytest unit tests for the following code to ensure 100% coverage.
    
    Code:
    {json.dumps(state['generated_code'], indent=2)}
    
    Output a JSON mapping the test file path to the test code.
    Example: {{"test_math_utils.py": "import pytest\\nfrom math_utils import ...\\n\\ndef test_add():\\n..."}}
    Ensure the test file names start with 'test_'.
    Do not output markdown block formatting around the JSON.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        test_files = extract_json(response.content)
        write_files(test_files)
        return {"test_files": test_files}
    except Exception as e:
        print(f"Error parsing test generation: {e}")
        return {"test_files": {}}

def test_executor(state: AgentState):
    print("--- TEST EXECUTOR ---")
    success, output = run_pytest(state.get("test_files", {}))
    print(f"Test Status: {'PASSED' if success else 'FAILED'}")
    return {"test_status": success, "test_output": output}

def healer_node(state: AgentState):
    print("--- HEALER NODE ---")
    iteration = state.get("iteration_count", 0) + 1
    print(f"Iteration: {iteration}")
    prompt = f"""
    You are an expert Python debugger.
    The previous code failed the unit tests.
    
    Code:
    {json.dumps(state['generated_code'], indent=2)}
    
    Test Output / Traceback:
    {state['test_output']}
    
    Task: {state['task_description']}
    
    Fix the code to make the tests pass. 
    Output the corrected code files as a JSON string mapping file paths to their new fixed content.
    Do not output markdown block formatting around the JSON.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        generated_code = extract_json(response.content)
        write_files(generated_code)
        return {
            "generated_code": generated_code,
            "iteration_count": iteration
        }
    except Exception as e:
        print(f"Error parsing healer generation: {e}")
        return {"iteration_count": iteration}

def hitl_gate(state: AgentState):
    print("--- HUMAN IN THE LOOP GATE ---")
    if state["test_status"]:
        print("Tests passed successfully.")
    else:
        print("Max iterations reached. Tests are still failing.")
        
    print("Execution paused. Awaiting human verification.")
    
    # In a real CLI with breakpoints, the graph would pause here.
    # For this script, we'll simulate an interactive prompt.
    user_input = input("Approve changes and create PR? (y/n): ")
    approved = user_input.lower().strip() == 'y'
    
    return {"human_approved": approved}

def git_pr_creator(state: AgentState):
    print("--- GIT PR CREATOR ---")
    if state.get("human_approved"):
        pr_url = create_git_pr()
        print(f"PR Created: {pr_url}")
        return {"pr_url": pr_url}
    else:
        print("PR creation skipped due to lack of human approval.")
        return {"pr_url": None}

def should_heal(state: AgentState):
    if state["test_status"] == True:
        return "hitl_gate"
    if state.get("iteration_count", 0) >= 3:
        print("Max iterations reached. Proceeding to HITL.")
        return "hitl_gate"
    return "healer_node"

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("planner_and_coder", planner_and_coder)
    workflow.add_node("test_generator", test_generator)
    workflow.add_node("test_executor", test_executor)
    workflow.add_node("healer_node", healer_node)
    workflow.add_node("hitl_gate", hitl_gate)
    workflow.add_node("git_pr_creator", git_pr_creator)
    
    workflow.set_entry_point("planner_and_coder")
    
    workflow.add_edge("planner_and_coder", "test_generator")
    workflow.add_edge("test_generator", "test_executor")
    
    workflow.add_conditional_edges(
        "test_executor",
        should_heal,
        {
            "healer_node": "healer_node",
            "hitl_gate": "hitl_gate"
        }
    )
    
    workflow.add_edge("healer_node", "test_executor")
    workflow.add_edge("hitl_gate", "git_pr_creator")
    workflow.add_edge("git_pr_creator", END)
    
    return workflow.compile()
