import os

import google.auth
from google.adk.agents import SequentialAgent

from app.agents.analyst_agent import analyst_agent
from app.agents.fixer_agent import fixer_agent
from app.agents.pentester_agent import pentester_agent
from app.utils.util import add_git_diff_to_state

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)  # type: ignore
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")  # type: ignore
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")  # type: ignore

root_agent = SequentialAgent(
    name="root_agent",
    sub_agents=[analyst_agent, fixer_agent, pentester_agent],
    before_agent_callback=add_git_diff_to_state,
)
