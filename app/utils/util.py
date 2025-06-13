from pathlib import Path

from google.adk.agents.callback_context import CallbackContext
from google.cloud import logging as google_cloud_logging

logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)


def load_prompt(prompt_name: str) -> str:
    """Loads a prompt from the prompts directory."""
    prompt_path = Path(__file__).parent.parent / "prompts" / f"{prompt_name}.md"
    with open(prompt_path) as f:
        return f.read()


def add_git_diff_to_state(callback_context: CallbackContext) -> None:
    """Adds the git diff to the state."""
    if "git_diff" not in callback_context.state.to_dict():
        callback_context.state["git_diff"] = callback_context.state["state"]["git_diff"]

    return None
