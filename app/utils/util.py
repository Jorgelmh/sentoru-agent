from pathlib import Path

from google.adk.agents.callback_context import CallbackContext
from google.cloud import logging as google_cloud_logging
from unidiff import PatchSet

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


def format_patch_for_display(patch: PatchSet) -> str:
    """Formats a PatchSet object into a markdown string, showing only added lines.

    Args:
        patch: A PatchSet object from the unidiff library.

    Returns:
        A markdown-formatted string of the diff's added lines.
    """
    markdown_output = []
    for patched_file in patch:
        # Check if there are any added lines in the file to determine if we should include it
        if patched_file.is_binary_file or not any(
            line.is_added for hunk in patched_file for line in hunk
        ):
            continue

        # Add a markdown header for the file path
        markdown_output.append(f"### `{patched_file.path}`")
        markdown_output.append("```diff")

        for hunk in patched_file:
            # Only include hunks that have added lines
            if not any(line.is_added for line in hunk):
                continue

            # Simplified hunk header showing only target file info
            hunk_header_info = f"@@ -... +{hunk.target_start},{hunk.target_length} @@"
            if hunk.section_header:
                hunk_header_info += f" {hunk.section_header}"
            markdown_output.append(hunk_header_info)

            for line in hunk:
                if line.is_added:
                    line_text = line.value.rstrip("\r\n")
                    markdown_output.append(f"{line.target_line_no: <4} {line_text}")

        markdown_output.append("```")
        markdown_output.append("")  # For spacing between files

    return "\n".join(markdown_output)


def format_git_diff_cb(callback_context: CallbackContext) -> None:
    """Formats the git diff by adding the line numbers to the diff, so the LLM Agent can
    correctly identify the lines that have been changed and where to place the
    suggestions.

    Note: This is crucial as the LLM is not able to properly determine the updated lines by itself directly from the git diff.
    It'd need to calculate the position of the lines in the file by counting the hunk lines, which is usually not efficient and error prone.
    """
    if "git_diff" not in callback_context.state.to_dict():
        return None
    path_set = PatchSet(callback_context.state["git_diff"])
    formatted_diff = format_patch_for_display(path_set)
    callback_context.state["git_diff"] = formatted_diff
    return None
