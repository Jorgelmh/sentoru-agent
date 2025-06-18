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

# mypy: disable-error-code="union-attr"
from pathlib import Path
from typing import Dict, Tuple

from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import pytest

from app.agent import root_agent


@pytest.fixture
def session_service():
    """Fixture to provide a session service for tests."""
    return InMemorySessionService()


@pytest.fixture
def vulnerable_git_diff():
    """Fixture to provide git diff with security vulnerabilities."""
    sample_diff_path = Path(__file__).parent.parent / "samples" / "sample.diff"
    with open(sample_diff_path) as f:
        return f.read()


@pytest.fixture
def clean_git_diff():
    """Fixture to provide git diff with clean, secure code."""
    sample_diff_path = Path(__file__).parent.parent / "samples" / "sample_clean.diff"
    with open(sample_diff_path) as f:
        return f.read()


@pytest.fixture
def runner_with_session(session_service):
    """Fixture to provide a runner with session service."""
    return Runner(agent=root_agent, session_service=session_service, app_name="test")


def extract_security_analysis_results(events) -> Tuple[list, Dict, bool, bool, bool]:
    """
    Helper function to extract security analysis results from agent events.
    
    Returns:
        Tuple of (fixed_code_patches, pen_tests, has_text_content, has_fixed_code_patches, has_pen_tests)
    """
    has_text_content = False
    has_fixed_code_patches = False
    has_pen_tests = False
    fixed_code_patches = []
    pen_tests = {}
    
    for event in events:
        # Check for text content
        if (
            event.content
            and event.content.parts
            and any(part.text for part in event.content.parts)
        ):
            has_text_content = True
            
        # Check for state updates with security analysis results
        if hasattr(event, 'actions') and event.actions:
            actions = event.actions
            if hasattr(actions, 'state_delta') and actions.state_delta:
                state_delta = actions.state_delta
                if "fixed_code_patches" in state_delta:
                    fixed_code_patches = state_delta["fixed_code_patches"]["patches"]
                    has_fixed_code_patches = True
                if "pen_tests" in state_delta:
                    pen_tests = state_delta["pen_tests"]
                    has_pen_tests = True
    
    return fixed_code_patches, pen_tests, has_text_content, has_fixed_code_patches, has_pen_tests


@pytest.mark.asyncio
async def test_agent_stream_with_vulnerabilities(session_service, runner_with_session, vulnerable_git_diff):
    """
    Integration test for the sentoku agent stream functionality with vulnerable code.
    Tests that the agent returns valid streaming responses for security analysis
    of git diffs with vulnerabilities, and produces non-empty security fixes and penetration tests.
    """
    # Create session with initial state containing the vulnerable git diff
    user_id = "test_user_vulnerable"
    session = await session_service.create_session(
        user_id=user_id, 
        app_name="test",
        state={"git_diff": vulnerable_git_diff}
    )
    
    # Use a security-focused prompt appropriate for the sentoku agent
    message = types.Content(
        role="user", 
        parts=[types.Part.from_text(text="Review PR code changes according to your instructions.")]
    )

    events = list(
        runner_with_session.run(
            new_message=message,
            user_id=user_id,
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    assert len(events) > 0, "Expected at least one message"

    # Extract results using helper function
    fixed_code_patches, pen_tests, has_text_content, has_fixed_code_patches, has_pen_tests = extract_security_analysis_results(events)
    
    # Basic assertions
    assert has_text_content, "Expected at least one message with text content"
    assert has_fixed_code_patches, "Expected fixed_code_patches in state delta"
    assert has_pen_tests, "Expected pen_tests in state delta"
    
    # Verify the structure of results (should be dictionaries even if empty)
    assert isinstance(fixed_code_patches, list), "fixed_code_patches should be a list of patches"
    assert isinstance(pen_tests, dict), "pen_tests should be a dictionary"
    
    # For vulnerable code, we should get non-empty results
    assert len(fixed_code_patches) > 0, "Expected non-empty fixed_code_patches for vulnerable code"
    assert len(pen_tests) > 0, "Expected non-empty pen_tests for vulnerable code"


@pytest.mark.asyncio
async def test_agent_stream_with_clean_code(session_service, runner_with_session, clean_git_diff):
    """
    Integration test for the sentoku agent with clean, secure code.
    Tests that the agent returns empty fixed_code_patches and pen_tests
    when no security vulnerabilities are found.
    """
    # Create session with initial state containing the clean git diff
    user_id = "test_user_clean"
    session = await session_service.create_session(
        user_id=user_id, 
        app_name="test",
        state={"git_diff": clean_git_diff}
    )
    
    message = types.Content(
        role="user", 
        parts=[types.Part.from_text(text="Review PR code changes according to your instructions.")]
    )

    events = list(
        runner_with_session.run(
            new_message=message,
            user_id=user_id,
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    assert len(events) > 0, "Expected at least one message"

    # Extract results using helper function
    fixed_code_patches, _, has_text_content, has_fixed_code_patches, _ = extract_security_analysis_results(events)
    
    # Basic assertions
    assert has_text_content, "Expected at least one message with text content"
    assert has_fixed_code_patches, "Expected fixed_code_patches in state delta"
    
    # Verify the structure of results
    assert isinstance(fixed_code_patches, list), "fixed_code_patches should be a list of patches"
    
    # For clean code, we should get empty results
    assert len(fixed_code_patches) == 0, "Expected empty fixed_code_patches for clean code"
