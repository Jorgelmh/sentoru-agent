import os

from google.adk.agents import LlmAgent

from app.utils.typing import FixerAgentOutput
from app.utils.util import format_git_diff_cb, load_prompt

fixer_agent = LlmAgent(
    name="VulnerabilityFixerAgent",
    model=os.environ.get("LLM_DEPLOYMENT", ""),
    instruction=load_prompt("fixer_agent"),
    description="Suggests or generates code changes to fix detected vulnerabilities.",
    output_key="fixed_code_patches",
    before_agent_callback=[format_git_diff_cb],
    output_schema=FixerAgentOutput,
)
