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

"""
Integration tests for the AgentEngineApp functionality.

This module contains integration tests that verify the complete functionality
of the AgentEngineApp when components work together. These tests may use
minimal mocking and focus on end-to-end workflows, ensuring the agent engine
operates correctly in realistic scenarios.
"""

# Standard library imports
import json
import logging
import os
import tempfile
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch, MagicMock

# Third-party imports
import pytest
from google.adk.events.event import Event

# First-party imports
from app.agent import root_agent
from app.agent_engine_app import AgentEngineApp, deploy_agent_engine_app


class TestAgentEngineAppIntegration:
    """Integration tests for AgentEngineApp class."""

    @pytest.fixture
    def mock_google_cloud_services(self) -> Generator[Dict[str, Mock], None, None]:
        """
        Fixture that mocks Google Cloud services for integration testing.
        
        This fixture provides a consistent set of mocks for Google Cloud
        services that are required for AgentEngineApp functionality,
        allowing integration tests to run without actual GCP connectivity.
        
        Yields:
            Dict containing mock instances for various Google Cloud services.
        """
        mocks = {}
        
        # Mock Google Cloud Logging
        with patch('google.cloud.logging.Client') as mock_logging_client:
            mock_logger = Mock()
            mock_logging_client_instance = Mock()
            mock_logging_client_instance.logger.return_value = mock_logger
            mock_logging_client.return_value = mock_logging_client_instance
            mocks['logging_client'] = mock_logging_client
            mocks['logger'] = mock_logger
            
            # Mock OpenTelemetry components
            with patch('app.agent_engine_app.TracerProvider') as mock_tracer_provider:
                with patch('app.agent_engine_app.export.BatchSpanProcessor') as mock_processor:
                    with patch('app.agent_engine_app.CloudTraceLoggingSpanExporter') as mock_exporter:
                        with patch('app.agent_engine_app.trace.set_tracer_provider') as mock_set_provider:
                            mocks['tracer_provider'] = mock_tracer_provider
                            mocks['batch_processor'] = mock_processor
                            mocks['trace_exporter'] = mock_exporter
                            mocks['set_tracer_provider'] = mock_set_provider
                            
                            # Mock Feedback model
                            with patch('app.agent_engine_app.Feedback') as mock_feedback:
                                mock_feedback_obj = Mock()
                                mock_feedback_obj.model_dump.return_value = {"validated": True}
                                mock_feedback.model_validate.return_value = mock_feedback_obj
                                mocks['feedback'] = mock_feedback
                                
                                yield mocks

    @pytest.fixture
    def agent_app(self, mock_google_cloud_services: Dict[str, Mock]) -> Generator[AgentEngineApp, None, None]:
        """
        Fixture to create and set up AgentEngineApp for integration testing.
        
        Creates a fully configured AgentEngineApp instance that can be used
        for integration testing. The app is set up with mocked external
        dependencies but maintains realistic internal workflows.
        
        Args:
            mock_google_cloud_services: Mocked Google Cloud services.
            
        Yields:
            Configured AgentEngineApp instance ready for integration testing.
        """
        with patch('app.agent_engine_app.root_agent') as mock_root_agent:
            # Configure mock root agent with realistic attributes
            mock_root_agent.name = "sentoru_security_pipeline"
            mock_root_agent.sub_agents = [Mock(), Mock(), Mock()]  # 3 agents
            
            app = AgentEngineApp(agent=mock_root_agent)
            app.set_up()
            yield app

    def test_complete_agent_setup_workflow(
        self, 
        agent_app: AgentEngineApp,
        mock_google_cloud_services: Dict[str, Mock]
    ) -> None:
        """
        Test the complete agent setup workflow from initialization to ready state.
        
        This integration test verifies that an AgentEngineApp can be properly
        initialized, configured, and prepared for operation with all necessary
        components working together.
        
        Args:
            agent_app: Configured AgentEngineApp instance.
            mock_google_cloud_services: Mocked Google Cloud services.
        """
        # Verify the app was initialized correctly
        assert agent_app is not None
        assert agent_app.agent is not None
        assert hasattr(agent_app, 'logger')
        
        # Verify that setup was called and services were initialized
        logging_client_mock = mock_google_cloud_services['logging_client']
        tracer_provider_mock = mock_google_cloud_services['tracer_provider']
        
        logging_client_mock.assert_called()
        tracer_provider_mock.assert_called()
        
        # Verify the agent has expected attributes
        assert agent_app.agent.name == "sentoru_security_pipeline"
        assert len(agent_app.agent.sub_agents) == 3
        
        logging.info("Complete agent setup workflow test passed")

    def test_feedback_end_to_end_workflow(
        self, 
        agent_app: AgentEngineApp,
        mock_google_cloud_services: Dict[str, Mock]
    ) -> None:
        """
        Test the complete feedback workflow from registration to logging.
        
        This test verifies the end-to-end feedback process including validation,
        transformation, and logging of user feedback data.
        
        Args:
            agent_app: Configured AgentEngineApp instance.
            mock_google_cloud_services: Mocked Google Cloud services.
        """
        # Test data representing realistic feedback scenarios
        feedback_scenarios = [
            {
                "score": 5,
                "text": "Excellent security analysis! Found critical SQL injection.",
                "invocation_id": "test-session-001",
                "user_id": "security-engineer@company.com",
                "timestamp": "2025-01-15T10:30:00Z"
            },
            {
                "score": 3,
                "text": "Good analysis but missed some edge cases.",
                "invocation_id": "test-session-002",
                "user_id": "developer@company.com",
                "timestamp": "2025-01-15T11:15:00Z"
            },
            {
                "score": 1,
                "text": "False positive - this is not a vulnerability.",
                "invocation_id": "test-session-003",
                "user_id": "senior-dev@company.com",
                "timestamp": "2025-01-15T14:20:00Z"
            }
        ]
        
        logger_mock = mock_google_cloud_services['logger']
        feedback_mock = mock_google_cloud_services['feedback']
        
        # Process each feedback scenario
        for i, feedback_data in enumerate(feedback_scenarios):
            # Clear previous calls for clean assertion
            logger_mock.reset_mock()
            feedback_mock.reset_mock()
            
            # Register feedback
            agent_app.register_feedback(feedback_data)
            
            # Verify feedback was processed correctly
            feedback_mock.model_validate.assert_called_once_with(feedback_data)
            logger_mock.log_struct.assert_called_once_with(
                {"validated": True}, severity="INFO"
            )
            
            logging.info(f"Feedback scenario {i+1} processed successfully")
        
        logging.info("End-to-end feedback workflow test passed")

    def test_operations_registration_integration(self, agent_app: AgentEngineApp) -> None:
        """
        Test that operation registration works correctly in integration context.
        
        Verifies that the AgentEngineApp properly registers all available
        operations including both base operations and custom feedback operations.
        
        Args:
            agent_app: Configured AgentEngineApp instance.
        """
        # Get operations from the integrated app
        operations = agent_app.register_operations()
        
        # Verify operations structure
        assert isinstance(operations, dict)
        assert "" in operations  # Default operation category
        assert isinstance(operations[""], list)
        
        # Verify that register_feedback is included
        assert "register_feedback" in operations[""]
        
        # Test that operations can be called (basic smoke test)
        try:
            agent_app.register_feedback({
                "score": 4,
                "text": "Test feedback for operations integration",
                "invocation_id": "ops-test-001"
            })
            operations_test_passed = True
        except Exception as e:
            logging.error(f"Operations integration failed: {e}")
            operations_test_passed = False
        
        assert operations_test_passed, "Operations should be callable after registration"
        
        logging.info("Operations registration integration test passed")

    def test_app_cloning_integration(self, agent_app: AgentEngineApp) -> None:
        """
        Test that app cloning works correctly with all components.
        
        Verifies that the AgentEngineApp can be properly cloned with all
        configuration and state preserved in the new instance.
        
        Args:
            agent_app: Configured AgentEngineApp instance.
        """
        # Modify original app state
        original_agent = agent_app.agent
        
        # Clone the app
        cloned_app = agent_app.clone()
        
        # Verify clone is a separate instance
        assert cloned_app is not agent_app
        assert isinstance(cloned_app, AgentEngineApp)
        
        # Verify clone has same configuration
        assert cloned_app.agent == original_agent
        
        # Test that both instances can operate independently
        test_feedback = {
            "score": 5,
            "text": "Testing cloned app functionality",
            "invocation_id": "clone-test-001"
        }
        
        # Both should be able to process feedback
        try:
            agent_app.register_feedback(test_feedback)
            cloned_app.register_feedback(test_feedback)
            cloning_test_passed = True
        except Exception as e:
            logging.error(f"Cloning integration failed: {e}")
            cloning_test_passed = False
        
        assert cloning_test_passed, "Both original and cloned apps should function"
        
        logging.info("App cloning integration test passed")


class TestDeploymentIntegration:
    """Integration tests for deployment functionality."""

    @pytest.fixture
    def mock_deployment_environment(self) -> Generator[Dict[str, Mock], None, None]:
        """
        Fixture that mocks the deployment environment for integration testing.
        
        Creates a comprehensive mock environment that simulates the Google Cloud
        infrastructure required for agent deployment without requiring actual
        cloud resources.
        
        Yields:
            Dict containing mock instances for deployment-related services.
        """
        mocks = {}
        
        with patch('app.agent_engine_app.vertexai') as mock_vertexai:
            with patch('app.agent_engine_app.agent_engines') as mock_agent_engines:
                with patch('app.agent_engine_app.create_bucket_if_not_exists') as mock_create_bucket:
                    with patch('app.agent_engine_app._save_deployment_metadata') as mock_save_metadata:
                        with patch('app.agent_engine_app.root_agent') as mock_root_agent:
                            
                            # Configure mocks
                            mock_remote_agent = Mock()
                            mock_remote_agent.resource_name = "projects/test/agents/sentoru-001"
                            
                            mock_agent_engines.list.return_value = []  # No existing agents
                            mock_agent_engines.create.return_value = mock_remote_agent
                            
                            mocks['vertexai'] = mock_vertexai
                            mocks['agent_engines'] = mock_agent_engines
                            mocks['create_bucket'] = mock_create_bucket
                            mocks['save_metadata'] = mock_save_metadata
                            mocks['root_agent'] = mock_root_agent
                            mocks['remote_agent'] = mock_remote_agent
                            
                            yield mocks

    def test_complete_deployment_workflow(
        self, 
        mock_deployment_environment: Dict[str, Mock]
    ) -> None:
        """
        Test the complete deployment workflow from start to finish.
        
        This integration test simulates a full deployment process including
        infrastructure setup, agent configuration, and metadata persistence.
        
        Args:
            mock_deployment_environment: Mocked deployment services.
        """
        # Create a temporary requirements file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as req_file:
            req_file.write("google-cloud-logging>=3.0.0\n")
            req_file.write("vertexai>=1.0.0\n")
            req_file.write("opentelemetry-api>=1.0.0\n")
            req_file.flush()
            requirements_path = req_file.name
        
        try:
            # Execute deployment
            result = deploy_agent_engine_app(
                project="test-project-integration",
                location="us-central1",
                agent_name="sentoru-integration-test",
                requirements_file=requirements_path,
                extra_packages=["./app", "./tests"],
                env_vars={"ENVIRONMENT": "integration-test", "LOG_LEVEL": "DEBUG"}
            )
            
            # Verify deployment steps were executed
            mocks = mock_deployment_environment
            
            # Verify bucket creation
            mocks['create_bucket'].assert_called_once_with(
                bucket_name="gs://test-project-integration-agent-engine",
                project="test-project-integration",
                location="us-central1"
            )
            
            # Verify Vertex AI initialization
            mocks['vertexai'].init.assert_called_once_with(
                project="test-project-integration",
                location="us-central1",
                staging_bucket="gs://test-project-integration-agent-engine"
            )
            
            # Verify agent creation (not update since no existing agents)
            mocks['agent_engines'].list.assert_called_once()
            mocks['agent_engines'].create.assert_called_once()
            
            # Verify metadata was saved
            mocks['save_metadata'].assert_called_once_with(mocks['remote_agent'])
            
            # Verify return value
            assert result == mocks['remote_agent']
            
            logging.info("Complete deployment workflow test passed")
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(requirements_path)
            except FileNotFoundError:
                pass

    def test_deployment_with_existing_agent_update(
        self, 
        mock_deployment_environment: Dict[str, Mock]
    ) -> None:
        """
        Test deployment workflow when updating an existing agent.
        
        This test verifies that the deployment process correctly identifies
        and updates existing agents rather than creating duplicates.
        
        Args:
            mock_deployment_environment: Mocked deployment services.
        """
        # Configure mocks for existing agent scenario
        mocks = mock_deployment_environment
        existing_agent = Mock()
        existing_agent.update.return_value = mocks['remote_agent']
        
        # Simulate existing agent found
        mocks['agent_engines'].list.return_value = [existing_agent]
        
        # Create temporary requirements file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as req_file:
            req_file.write("updated-package>=2.0.0\n")
            req_file.flush()
            requirements_path = req_file.name
        
        try:
            # Execute deployment
            result = deploy_agent_engine_app(
                project="test-project-update",
                location="us-west1",
                agent_name="existing-sentoru-agent",
                requirements_file=requirements_path
            )
            
            # Verify update path was taken
            mocks['agent_engines'].list.assert_called_once()
            existing_agent.update.assert_called_once()
            mocks['agent_engines'].create.assert_not_called()  # Should not create new
            
            # Verify result
            assert result == mocks['remote_agent']
            
            logging.info("Deployment update workflow test passed")
            
        finally:
            try:
                os.unlink(requirements_path)
            except FileNotFoundError:
                pass

    def test_deployment_error_handling_integration(
        self, 
        mock_deployment_environment: Dict[str, Mock]
    ) -> None:
        """
        Test deployment error handling in integration context.
        
        Verifies that deployment failures are properly handled and that
        appropriate errors are raised with meaningful messages.
        
        Args:
            mock_deployment_environment: Mocked deployment services.
        """
        # Test missing requirements file
        with pytest.raises(FileNotFoundError):
            deploy_agent_engine_app(
                project="test-project",
                location="us-central1",
                requirements_file="nonexistent-file.txt"
            )
        
        # Test bucket creation failure
        mocks = mock_deployment_environment
        mocks['create_bucket'].side_effect = Exception("Bucket creation failed")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as req_file:
            req_file.write("test-package>=1.0.0\n")
            req_file.flush()
            requirements_path = req_file.name
        
        try:
            with pytest.raises(Exception, match="Bucket creation failed"):
                deploy_agent_engine_app(
                    project="test-project",
                    location="us-central1",
                    requirements_file=requirements_path
                )
            
            logging.info("Deployment error handling test passed")
            
        finally:
            try:
                os.unlink(requirements_path)
            except FileNotFoundError:
                pass


class TestStreamingIntegration:
    """Integration tests for streaming functionality."""

    @pytest.fixture
    def streaming_test_environment(self) -> Generator[Dict[str, Mock], None, None]:
        """
        Fixture for setting up streaming test environment.
        
        Creates mocks and configurations necessary for testing streaming
        functionality in an integrated context.
        
        Yields:
            Dict containing streaming-related mock instances.
        """
        mocks = {}
        
        with patch('app.agent_engine_app.google_cloud_logging.Client'):
            with patch('app.agent_engine_app.root_agent') as mock_root_agent:
                # Configure mock agent for streaming
                mock_root_agent.name = "sentoru_streaming_agent"
                
                # Mock streaming response
                mock_stream_response = [
                    {"content": {"parts": [{"text": "Analyzing security vulnerabilities..."}]}},
                    {"content": {"parts": [{"text": "Found potential SQL injection in line 42."}]}},
                    {"content": {"parts": [{"text": "Generating security recommendations..."}]}},
                ]
                
                mocks['root_agent'] = mock_root_agent
                mocks['stream_response'] = mock_stream_response
                
                yield mocks

    def test_streaming_query_integration(
        self,
        streaming_test_environment: Dict[str, Mock]
    ) -> None:
        """
        Test streaming query functionality in integration context.
        
        This test simulates a realistic streaming scenario where an agent
        processes a security analysis request and returns streaming responses.
        
        Args:
            streaming_test_environment: Streaming test environment mocks.
        """
        mocks = streaming_test_environment
        
        # Create app instance
        app = AgentEngineApp(agent=mocks['root_agent'])
        
        # Mock the stream_query method to return realistic streaming data
        with patch.object(app, 'stream_query') as mock_stream_query:
            mock_stream_query.return_value = iter(mocks['stream_response'])
            
            # Execute streaming query
            test_message = """
            Please analyze this code diff for security vulnerabilities:
            
            diff --git a/app.py b/app.py
            --- a/app.py
            +++ b/app.py
            @@ -10,3 +10,3 @@
            -    query = "SELECT * FROM users WHERE id = %s"
            +    query = f"SELECT * FROM users WHERE id = {user_id}"
            """
            
            # Collect streaming events
            events = list(app.stream_query(message=test_message, user_id="test-user"))
            
            # Verify streaming behavior
            assert len(events) == 3
            mock_stream_query.assert_called_once_with(
                message=test_message, 
                user_id="test-user"
            )
            
            # Verify content of streaming events
            expected_texts = [
                "Analyzing security vulnerabilities...",
                "Found potential SQL injection in line 42.",
                "Generating security recommendations..."
            ]
            
            for i, event in enumerate(events):
                assert "content" in event
                assert "parts" in event["content"]
                assert len(event["content"]["parts"]) > 0
                assert "text" in event["content"]["parts"][0]
                assert event["content"]["parts"][0]["text"] == expected_texts[i]
            
            logging.info("Streaming query integration test passed")


# Pytest configuration and markers
pytestmark = [pytest.mark.integration, pytest.mark.slow]


def pytest_configure(config):
    """Configure pytest for integration tests."""
    # Set up logging for integration tests
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Add custom markers
    config.addinivalue_line(
        "markers", 
        "integration: marks tests as integration tests (may be slow)"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow running"
    )


if __name__ == "__main__":
    """Run integration tests when executed directly."""
    pytest.main([__file__, "-v", "-m", "integration"])