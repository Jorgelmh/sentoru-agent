import os

import google.auth
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.agent_tool import AgentTool

from app.agents.analyst_agent import analyst_agent
from app.agents.fixer_agent import fixer_agent
from app.agents.pentester_agent import pentester_agent
from app.tools import get_rag_vulnerability_knowledge_tool
from app.utils.util import add_git_diff_to_state, load_prompt

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)  # type: ignore
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")  # type: ignore
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")  # type: ignore

search_agent = LlmAgent(
    name="SearchAgent",
    model=os.environ.get("LLM_DEPLOYMENT", "gemini-2.0-flash"),
    instruction=load_prompt("search_agent"),
    description="Searches for relevant cybersecurity vulnerability advise for mitigations.",
    output_key="search_report",
    tools=[get_rag_vulnerability_knowledge_tool()],
)

review_agent = SequentialAgent(
    name="review_agent",
    sub_agents=[analyst_agent, fixer_agent, pentester_agent],
    before_agent_callback=add_git_diff_to_state,
)

root_agent = LlmAgent(
    name="root_agent",
    model=os.environ.get("LLM_DEPLOYMENT", "gemini-2.0-flash"),
    instruction=load_prompt("orchestrator_agent"),
    sub_agents=[review_agent],
    tools=[AgentTool(agent=search_agent)],
    before_agent_callback=add_git_diff_to_state,
)
