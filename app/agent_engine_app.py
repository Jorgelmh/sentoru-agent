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
"""Agent Engine Application for Sentoru Security Agent.

This module provides the main application class and deployment functionality for running
the Sentoru security agent on Google Cloud Vertex AI.
"""

# mypy: disable-error-code="attr-defined"

# Standard library imports
import argparse
import datetime
import json
import logging
import os
from collections.abc import Mapping, Sequence
from typing import Any

# Third-party imports
import google.auth
import vertexai
from google.cloud import logging as google_cloud_logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, export
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

# First-party imports
from app.agent import root_agent
from app.utils.gcs import create_bucket_if_not_exists
from app.utils.tracing import CloudTraceLoggingSpanExporter
from app.utils.typing import Feedback


class AgentEngineApp(AdkApp):
    """Agent Engine Application wrapper for Vertex AI deployment.

    This class extends the ADK (Agent Development Kit) application to provide enhanced
    logging, tracing, and feedback collection capabilities for the Sentoru security
    agent.
    """

    def __init__(self, agent, **kwargs):
        """Initialize the AgentEngineApp with the specified agent.

        Args:
            agent: The agent instance to be used by this application.
            **kwargs: Additional arguments passed to the parent class.
        """
        super().__init__(agent=agent, **kwargs)
        # Store agent reference for backward compatibility
        self.agent = agent

    def set_up(self) -> None:
        """Initialize logging and tracing infrastructure.

        Sets up Google Cloud Logging and OpenTelemetry tracing to monitor agent
        execution and performance in the cloud environment.
        """
        super().set_up()

        # Initialize Google Cloud Logging
        logging_client = google_cloud_logging.Client()
        self.logger = logging_client.logger(__name__)

        # Configure OpenTelemetry tracing
        provider = TracerProvider()
        processor = export.BatchSpanProcessor(
            CloudTraceLoggingSpanExporter(
                project_id=os.environ.get("GOOGLE_CLOUD_PROJECT")
            )
        )
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

    def register_feedback(self, feedback: dict[str, Any]) -> None:
        """Collect and log user feedback for agent improvements.

        Args:
            feedback: Dictionary containing feedback data that will be
                     validated against the Feedback model and logged.
        """
        feedback_obj = Feedback.model_validate(feedback)
        self.logger.log_struct(feedback_obj.model_dump(), severity="INFO")

    def register_operations(self) -> Mapping[str, Sequence]:  # type: ignore
        """Register available operations for the agent engine.

        Extends the base operations to include feedback registration
        functionality alongside the core agent operations.

        Returns:
            Mapping of operation categories to their available methods.
        """
        operations = super().register_operations()
        operations[""] = operations[""] + ["register_feedback"]
        return operations

    def clone(self) -> "AgentEngineApp":
        """Create a deep copy of the agent engine application.

        Returns:
            A new instance of AgentEngineApp with the same configuration
            as the current instance.
        """
        template_attributes = self._tmpl_attrs
        new_app = self.__class__(
            agent=template_attributes.get("agent"),
            enable_tracing=template_attributes.get("enable_tracing"),
            session_service_builder=template_attributes.get("session_service_builder"),
            artifact_service_builder=template_attributes.get("artifact_service_builder"),
            env_vars=template_attributes.get("env_vars"),
        )
        new_app.set_up()
        return new_app


def deploy_agent_engine_app(
    project: str,
    location: str,
    agent_name: str | None = None,
    requirements_file: str = ".requirements.txt",
    extra_packages: list[str] | None = None,
    env_vars: dict[str, str] | None = None,
) -> agent_engines.AgentEngine:
    """Deploy the Sentoru agent to Vertex AI Agent Engine.

    This function handles the complete deployment process including:
    - Setting up Google Cloud Storage bucket for staging
    - Reading and processing requirements
    - Creating or updating the agent engine
    - Saving deployment metadata

    Args:
        project: Google Cloud Project ID where the agent will be deployed.
        location: Google Cloud region for deployment (e.g., 'us-central1').
        agent_name: Display name for the deployed agent. Defaults to None.
        requirements_file: Path to the requirements file.
                          Defaults to '.requirements.txt'.
        extra_packages: Additional Python packages to include in deployment.
                       Defaults to ['./app'].
        env_vars: Environment variables to set in the deployed agent.
                 Defaults to empty dict.

    Returns:
        The deployed AgentEngine instance from Vertex AI.

    Raises:
        FileNotFoundError: If the requirements file doesn't exist.
        google.auth.exceptions.GoogleAuthError: If authentication fails.
    """
    # Set default values for mutable arguments
    if extra_packages is None:
        extra_packages = ["./app"]
    if env_vars is None:
        env_vars = {}

    # Configure staging bucket for deployment artifacts
    staging_bucket = f"gs://{project}-agent-engine"

    create_bucket_if_not_exists(
        bucket_name=staging_bucket,
        project=project,
        location=location
    )

    vertexai.init(
        project=project,
        location=location,
        staging_bucket=staging_bucket
    )

    # Read and parse requirements file
    try:
        with open(requirements_file, encoding="utf-8") as f:
            requirements = f.read().strip().split("\n")
    except FileNotFoundError as e:
        logging.error(f"Requirements file not found: {requirements_file}")
        raise e

    # Initialize the agent engine application
    agent_engine = AgentEngineApp(agent=root_agent)

    # Configure worker parallelism for consistent execution
    env_vars["NUM_WORKERS"] = "1"

    # Prepare agent configuration
    agent_config = {
        "agent_engine": agent_engine,
        "display_name": agent_name,
        "description": (
            "A base ReAct agent built with Google's Agent Development Kit "
            "(ADK) for automated security code analysis"
        ),
        "extra_packages": extra_packages,
        "env_vars": env_vars,
        "requirements": requirements,
    }

    logging.info(f"Agent configuration: {agent_config}")

    # Deploy or update the agent
    existing_agents = list(
        agent_engines.list(filter=f"display_name={agent_name}")
    )

    if existing_agents:
        logging.info(f"Updating existing agent: {agent_name}")
        remote_agent = existing_agents[0].update(**agent_config)
    else:
        logging.info(f"Creating new agent: {agent_name}")
        remote_agent = agent_engines.create(**agent_config)

    # Save deployment metadata
    _save_deployment_metadata(remote_agent)

    return remote_agent


def _save_deployment_metadata(remote_agent: agent_engines.AgentEngine) -> None:
    """Save deployment metadata to a local JSON file.

    Args:
        remote_agent: The deployed agent engine instance.
    """
    config = {
        "remote_agent_engine_id": remote_agent.resource_name,
        "deployment_timestamp": datetime.datetime.now().isoformat(),
    }

    config_file = "deployment_metadata.json"

    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        logging.info(f"Agent Engine ID written to {config_file}")
    except OSError as e:
        logging.error(f"Failed to write deployment metadata: {e}")
        raise e


def _parse_environment_variables(env_vars_str: str) -> dict[str, str]:
    """Parse environment variables from command-line string format.

    Args:
        env_vars_str: Comma-separated string of KEY=VALUE pairs.

    Returns:
        Dictionary of environment variable names to values.

    Raises:
        ValueError: If the format is invalid.
    """
    env_vars = {}

    for pair in env_vars_str.split(","):
        try:
            key, value = pair.split("=", 1)
            env_vars[key.strip()] = value.strip()
        except ValueError as e:
            raise ValueError(
                f"Invalid environment variable format: {pair}. "
                "Expected KEY=VALUE format."
            ) from e

    return env_vars


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Deploy Sentoru agent engine app to Vertex AI"
    )

    parser.add_argument(
        "--project",
        default=None,
        help="GCP project ID (defaults to application default credentials)",
    )

    parser.add_argument(
        "--location",
        default="us-central1",
        help="GCP region (defaults to us-central1)",
    )

    parser.add_argument(
        "--agent-name",
        default="sentoru-agent",
        help="Name for the agent engine",
    )

    parser.add_argument(
        "--requirements-file",
        default=".requirements.txt",
        help="Path to requirements.txt file",
    )

    parser.add_argument(
        "--extra-packages",
        nargs="+",
        default=["./app"],
        help="Additional packages to include",
    )

    parser.add_argument(
        "--set-env-vars",
        help=(
            "Comma-separated list of environment variables "
            "in KEY=VALUE format"
        ),
    )

    return parser


def main() -> None:
    """Main entry point for command-line deployment.

    Parses command-line arguments and initiates the agent deployment process to Vertex
    AI.
    """
    parser = _create_argument_parser()
    args = parser.parse_args()

    # Parse environment variables if provided
    env_vars = {}
    if args.set_env_vars:
        try:
            env_vars = _parse_environment_variables(args.set_env_vars)
        except ValueError as e:
            logging.error(f"Environment variable parsing failed: {e}")
            return

    # Get project ID from default credentials if not provided
    if not args.project:
        try:
            _, args.project = google.auth.default()
        except google.auth.exceptions.GoogleAuthError as e:
            logging.error(f"Failed to get default project: {e}")
            return

    # Display deployment banner
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║       DEPLOYING AGENT TO VERTEX AI AGENT ENGINE          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    try:
        deploy_agent_engine_app(
            project=args.project,
            location=args.location,
            agent_name=args.agent_name,
            requirements_file=args.requirements_file,
            extra_packages=args.extra_packages,
            env_vars=env_vars,
        )
        print("Deployment completed successfully!")

    except Exception as e:
        logging.error(f"Deployment failed: {e}")
        print(f"Deployment failed: {e}")


if __name__ == "__main__":
    main()
