import os
from pathlib import Path
from google.adk.agents import LlmAgent

from app.types import FixerAgentOutput

# Load the instructions prompt
with open(Path(__file__).parent.parent / "prompts" / "fixer_agent.md", "r") as f:
    instruction = f.read()

fixer_agent = LlmAgent(
    name="VulnerabilityFixerAgent",
    model=os.environ.get("LLM_DEPLOYMENT", ""),
    instruction=instruction,
    description="Suggests or generates code changes to fix detected vulnerabilities.",
    output_key="fixed_code_patches",
    output_schema=FixerAgentOutput,
)
