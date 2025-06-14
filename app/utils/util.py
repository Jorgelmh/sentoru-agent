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


def add_line_numbers_to_diff(diff_text: str) -> str:
    """Adds line numbers to each line in the diff hunk."""
    lines = diff_text.splitlines()
    processed_diff = []
    in_hunk = False
    line_counter = 1

    for line in lines:
        if line.startswith("diff --git"):
            in_hunk = False
            processed_diff.append(line)
        elif line.startswith("@@"):
            in_hunk = True
            line_counter = 1
            processed_diff.append(line)
        elif in_hunk:
            # Any line inside a hunk that is not a 'no newline' message should be numbered.
            if line.startswith(
                "\\"
            ):  # In diff, this is for '\ No newline at end of file'
                processed_diff.append(line)
            else:
                processed_diff.append(f"{line_counter:<4}{line}")
                line_counter += 1
        else:
            processed_diff.append(line)

    return "\n".join(processed_diff)


def format_git_diff_cb(callback_context: CallbackContext) -> None:
    """Formats the git diff to add line numbers."""
    diff_text = callback_context.state["git_diff"]
    formatted_diff = add_line_numbers_to_diff(diff_text)
    callback_context.state["git_diff"] = formatted_diff
    return None
