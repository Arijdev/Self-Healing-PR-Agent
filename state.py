from typing import TypedDict, Dict, List, Optional

class AgentState(TypedDict):
    """
    Represents the state of our self-healing agent.
    """
    task_description: str
    target_files: List[str]
    generated_code: Dict[str, str]
    test_files: Dict[str, str]
    test_output: str
    test_status: bool
    iteration_count: int
    human_approved: bool
    pr_url: Optional[str]
