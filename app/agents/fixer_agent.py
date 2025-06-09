import os
from google.adk.agents import LlmAgent
from app.utils.util import load_prompt

from app.utils.typing import FixerAgentOutput

fixer_agent = LlmAgent(
    name="VulnerabilityFixerAgent",
    model=os.environ.get("LLM_DEPLOYMENT", ""),
    instruction=load_prompt("fixer_agent"),
    description="Suggests or generates code changes to fix detected vulnerabilities.",
    output_key="fixed_code_patches",
    output_schema=FixerAgentOutput,
)
