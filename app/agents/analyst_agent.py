import os

from google.adk.agents import LlmAgent

from app.tools import get_rag_vulnerability_knowledge_tool, get_safety_API_tool
from app.utils.util import load_prompt

analyst_agent = LlmAgent(
    name="AnalystAgent",
    model=os.environ.get("LLM_DEPLOYMENT", "gemini-2.0-flash"),
    instruction=load_prompt("analyst_agent"),
    description="Analyzes the codebase and identifies vulnerabilities.",
    tools=[get_safety_API_tool(), get_rag_vulnerability_knowledge_tool()],
    output_key="analysis",
)
