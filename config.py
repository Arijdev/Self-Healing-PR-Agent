import os
from dotenv import load_dotenv

from pathlib import Path

# Try importing streamlit to check secrets
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

# Load environment variables from .env file if present
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

def get_config(key, default=None):
    if HAS_STREAMLIT:
        try:
            # st.secrets might throw an exception if not running in a streamlit context or if secret doesn't exist
            # We catch Exception broadly to gracefully fallback to os.environ
            if key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass
    return os.environ.get(key, default)

# Configuration variables
GEMINI_API_KEY = get_config("GEMINI_API_KEY")
GITHUB_TOKEN = get_config("GITHUB_TOKEN")
REPO_PATH = get_config("REPO_PATH", ".")
TARGET_REPO_URL = get_config("TARGET_REPO_URL", "")

# Ensure critical variables are set
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY is not set. The LLM nodes will fail.")
