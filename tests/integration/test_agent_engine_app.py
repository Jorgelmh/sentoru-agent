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
"""Integration tests for the AgentEngineApp functionality.

This module contains tests that verify the core functionality of the AgentEngineApp,
including streaming queries, feedback registration, and agent initialization. These
tests ensure the agent engine works correctly in the ADK (Agent Development Kit)
environment.
"""

# Standard library imports
import logging
from typing import Generator

# Third-party imports
import pytest
from google.adk.events.event import Event

# First-party imports
from app.agent import root_agent
from app.agent_engine_app import AgentEngineApp


@pytest.fixture
def agent_app() -> Generator[AgentEngineApp, None, None]:
    """Fixture to create and set up AgentEngineApp instance.

    Creates a properly configured AgentEngineApp instance with the root
    agent and performs necessary setup including logging and tracing
    configuration. The fixture ensures clean setup and teardown for
    each test.

    Yields:
        AgentEngineApp: Configured and initialized agent engine app.

    Note:
        This fixture automatically handles the setup() call to initialize
        logging and tracing infrastructure required for agent operation.
    """
    app = AgentEngineApp(agent=root_agent)
    app.set_up()
    yield app
    # Cleanup could be added here if needed in the future


def test_agent_stream_query(agent_app: AgentEngineApp) -> None:
    """Integration test for the agent stream query functionality.

    This test verifies that the AgentEngineApp can handle streaming queries
    and return valid streaming responses. It sends a test message and
    validates the response structure and content.

    The test ensures:
    - At least one streaming event is generated
    - Events contain valid text content
    - Event structure conforms to expected format
    - No exceptions are raised during streaming

    Args:
        agent_app: Configured AgentEngineApp instance from fixture.

    Raises:
        AssertionError: If streaming doesn't work as expected.
    """
    # Create a test message for the stream query
    test_message = "What's the weather in San Francisco?"

    # Execute the streaming query and collect events
    events = list(agent_app.stream_query(message=test_message, user_id="test"))

    assert len(events) > 0, "Expected at least one chunk in response"

    # Validate that we have meaningful content in the response
    has_text_content = False
    valid_events_count = 0

    for event in events:
        try:
            # Validate event structure
            validated_event = Event.model_validate(event)
            valid_events_count += 1

            content = validated_event.content
            if (
                content is not None
                and content.parts
                and any(part.text for part in content.parts)
            ):
                has_text_content = True
                # Log first text content for debugging
                if not hasattr(test_agent_stream_query, '_logged_content'):
                    for part in content.parts:
                        if part.text:
                            logging.info(f"Sample response content: {part.text[:100]}...")
                            test_agent_stream_query._logged_content = True
                            break
                break

        except Exception as e:
            logging.warning(f"Failed to validate event: {e}")
            continue

    assert valid_events_count > 0, "Expected at least one valid event structure"
    assert has_text_content, "Expected at least one event with text content"

    logging.info(f"Stream query test passed with {valid_events_count} valid events")


def test_agent_feedback(agent_app: AgentEngineApp) -> None:
    """Integration test for the agent feedback functionality.

    This test verifies that the AgentEngineApp can properly handle feedback
    registration, including both valid and invalid feedback scenarios.
    It ensures proper validation and error handling for feedback data.

    The test covers:
    - Valid feedback registration
    - Invalid feedback rejection with appropriate errors
    - Feedback data validation against expected schema
    - Proper logging of feedback events

    Args:
        agent_app: Configured AgentEngineApp instance from fixture.

    Raises:
        AssertionError: If feedback handling doesn't work as expected.
    """
    # Test valid feedback registration
    valid_feedback_data = {
        "score": 5,
        "text": "Great response! The agent provided helpful security analysis.",
        "invocation_id": "test-run-123",
    }

    # This should not raise any exceptions
    try:
        agent_app.register_feedback(valid_feedback_data)
        logging.info("Valid feedback registered successfully")
    except Exception as e:
        pytest.fail(f"Valid feedback registration failed: {e}")

    # Test feedback with different score values
    for score in [1, 3, 5]:
        feedback_data = {
            "score": score,
            "text": f"Test feedback with score {score}",
            "invocation_id": f"test-run-{score}",
        }

        try:
            agent_app.register_feedback(feedback_data)
        except Exception as e:
            pytest.fail(f"Feedback with score {score} failed: {e}")

    # Test invalid feedback scenarios
    invalid_feedback_scenarios = [
        {
            "data": {
                "score": "invalid",  # Score must be numeric
                "text": "Bad feedback",
                "invocation_id": "test-run-invalid-score",
            },
            "description": "invalid score type"
        },
        {
            "data": {
                "score": 10,  # Assuming score should be 1-5
                "text": "Feedback with out-of-range score",
                "invocation_id": "test-run-invalid-range",
            },
            "description": "out-of-range score"
        },
        {
            "data": {
                # Missing required fields
                "text": "Incomplete feedback",
            },
            "description": "missing required fields"
        }
    ]

    for scenario in invalid_feedback_scenarios:
        with pytest.raises((ValueError, TypeError, KeyError)) as exc_info:
            agent_app.register_feedback(scenario["data"])

        logging.info(
            f"Expected validation error for {scenario['description']}: "
            f"{exc_info.value}"
        )

    logging.info("All assertions passed for agent feedback test")


def test_agent_app_initialization(agent_app: AgentEngineApp) -> None:
    """Test that AgentEngineApp initializes correctly with proper configuration.

    This test verifies that the AgentEngineApp instance is properly
    initialized with the correct agent, has necessary attributes,
    and can perform basic operations without errors.

    Args:
        agent_app: Configured AgentEngineApp instance from fixture.
    """
    # Verify the app is properly initialized
    assert agent_app is not None, "AgentEngineApp should be initialized"
    assert agent_app.agent is not None, "AgentEngineApp should have an agent"
    assert agent_app.agent == root_agent, "Should use the root_agent"

    # Verify that setup was called (should have logger attribute)
    assert hasattr(agent_app, 'logger'), "AgentEngineApp should have logger after setup"

    # Test that the app can be cloned
    cloned_app = agent_app.clone()
    assert cloned_app is not None, "Should be able to clone the app"
    assert cloned_app.agent == agent_app.agent, "Cloned app should have same agent"

    logging.info("Agent app initialization test passed")


def test_agent_operations_registration(agent_app: AgentEngineApp) -> None:
    """Test that AgentEngineApp properly registers its operations.

    This test verifies that the AgentEngineApp correctly registers
    its available operations, including the feedback registration
    functionality that extends the base operations.

    Args:
        agent_app: Configured AgentEngineApp instance from fixture.
    """
    # Get registered operations
    operations = agent_app.register_operations()

    assert operations is not None, "Should return operations mapping"
    assert isinstance(operations, dict), "Operations should be a dictionary"

    # Check that feedback registration is included
    base_operations = operations.get("", [])
    assert "register_feedback" in base_operations, (
        "Should include register_feedback operation"
    )

    logging.info(f"Registered operations: {operations}")
    logging.info("Agent operations registration test passed")


# Test helper functions
def create_test_message(content: str) -> str:
    """Create a test message for agent testing.

    Args:
        content: The message content to send to the agent.

    Returns:
        str: Formatted test message.
    """
    return f"Test query: {content}"


def validate_event_structure(event: dict) -> bool:
    """Validate that an event has the expected structure.

    Args:
        event: Event dictionary to validate.

    Returns:
        bool: True if event structure is valid, False otherwise.
    """
    try:
        validated_event = Event.model_validate(event)
        return True
    except Exception:
        return False


# Test configuration and markers
pytestmark = pytest.mark.integration


# Module-level test configuration
def pytest_configure():
    """Configure pytest for this test module."""
    logging.basicConfig(level=logging.INFO)
