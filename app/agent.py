# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import google.auth
from google.adk.agents import SequentialAgent

from app.agents.analysis_agent import analysis_agent
from app.agents.fixer_agent import fixer_agent
from app.agents.pentester_agent import pentester_agent
from app.utils.util import add_git_diff_to_state

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)  # type: ignore
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")  # type: ignore
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")  # type: ignore

root_agent = SequentialAgent(
    name="root_agent",
    sub_agents=[analysis_agent, fixer_agent, pentester_agent],
    before_agent_callback=add_git_diff_to_state,
)
