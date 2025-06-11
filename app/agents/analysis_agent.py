import os

from google.adk.agents import LlmAgent

from app.tools import get_safety_API_tool
from app.utils.util import load_prompt

analysis_agent = LlmAgent(
    name="AnalysisAgent",
    model=os.environ.get("LLM_DEPLOYMENT", ""),
    instruction=load_prompt("analysis_agent"),
    description="Analyzes the codebase and identifies vulnerabilities.",
    tools=[get_safety_API_tool()],
    output_key="analysis",
)
