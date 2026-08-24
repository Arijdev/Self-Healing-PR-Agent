import os
import subprocess
from pathlib import Path
from git import Repo
from datetime import datetime
from config import GITHUB_TOKEN, REPO_PATH

def read_files(file_paths: list[str]) -> dict[str, str]:
    """Reads the content of target files."""
    content = {}
    for path in file_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content[path] = f.read()
        except FileNotFoundError:
            content[path] = "" # Handle new file case
    return content

def write_files(files_dict: dict[str, str]) -> None:
    """Writes the generated code and tests to disk."""
    for path, content in files_dict.items():
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

def run_pytest(test_files: dict[str, str]) -> tuple[bool, str]:
    """Executes pytest in a subprocess and captures output."""
    test_paths = list(test_files.keys())
    if not test_paths:
        return True, "No test files to run."
    
    cmd = ["pytest"] + test_paths
    try:
        result = subprocess.run(
            cmd,
            cwd=REPO_PATH,
            capture_output=True,
            text=True
        )
        output = result.stdout
        if result.stderr:
            output += "\n--- STDERR ---\n" + result.stderr
        return result.returncode == 0, output
    except Exception as e:
        return False, f"Failed to run pytest: {str(e)}"

def create_git_pr(branch_prefix="fix/agent-refactor") -> str:
    """Creates a new branch, commits changes, and simulates opening a PR."""
    try:
        repo = Repo(REPO_PATH)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        branch_name = f"{branch_prefix}-{timestamp}"
        
        if repo.is_dirty(untracked_files=True):
            # Create and checkout new branch
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
            
            # Add all changes
            repo.git.add(A=True)
            
            # Commit
            repo.index.commit("Auto-generated changes by Self-Healing Agent")
            
            # Note: Actual PR creation requires pushing to remote and using GitHub API.
            # Mocking the PR URL for this demonstration.
            return f"https://github.com/mock/repo/pull/mock-{timestamp}"
        else:
            return "No changes to commit."
            
    except Exception as e:
        print(f"Git operation failed: {e}")
        return ""
