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
"""Security Analysis Tools for Sentoru Agent System.

This module provides tools for security vulnerability detection and analysis, including
RAG-based knowledge retrieval and dependency vulnerability scanning. The tools integrate
with external services to enhance the agent's security analysis capabilities through
Vertex AI and Safety CLI services.
"""

# Standard library imports
import os

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from google.cloud import logging as google_cloud_logging
from vertexai.preview import rag

from app.utils.util import load_prompt

logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)


def get_rag_vulnerability_knowledge_tool() -> VertexAiRagRetrieval:
    """Create a RAG-based tool for retrieving cybersecurity knowledge and best
    practices.

    This tool provides access to a curated knowledge base of security vulnerabilities,
    best practices, and remediation guidance using Vertex AI's Retrieval-Augmented
    Generation (RAG) capabilities. It searches through comprehensive security
    documentation to find relevant information based on code changes.

    The tool is designed to enhance security analysis by providing contextual
    information about:
    - OWASP Top 10 vulnerabilities and mitigation strategies
    - Common Weakness Enumeration (CWE) database entries
    - Python-specific security issues and solutions
    - General secure coding best practices and guidelines
    - Industry-standard security frameworks and methodologies

    Configuration:
    - similarity_top_k=10: Returns up to 10 most relevant documents
    - vector_distance_threshold=0.6: Filters for documents with ≥60% similarity
    - Uses semantic search to find contextually relevant security information

    Returns:
        VertexAiRagRetrieval: Configured RAG tool for vulnerability knowledge
            retrieval that can be used by security analysis agents.

    Environment Variables:
        VULN_RAG_CORPUS (str): The Vertex AI RAG corpus ID containing the
            security knowledge base. This corpus should be pre-populated
            with cybersecurity documentation and best practices.

    Raises:
        ValueError: If VULN_RAG_CORPUS environment variable is not set.
        ConnectionError: If unable to connect to Vertex AI RAG service.

    Example:
        When analyzing code with potential SQL injection:

        Query: "SQL injection in Python database queries"

        Response: Documents about parameterized queries, ORM usage,
        input validation, and specific Python libraries for safe DB access.

    Note:
        The RAG corpus should be regularly updated with the latest security
        advisories and best practices to ensure current and relevant responses.
    """

    vuln_rag_corpus = os.environ.get("VULN_RAG_CORPUS", "").strip()
    if not vuln_rag_corpus:
        raise ValueError(
            "VULN_RAG_CORPUS environment variable is required for RAG-based "
            "vulnerability knowledge retrieval. Please set it to your "
            "Vertex AI RAG corpus ID containing security documentation."
        )


    return VertexAiRagRetrieval(
        name="retrieve_vulnerability_knowledge",
        description=(
            "Use this tool to retrieve comprehensive documentation, best practices, "
            "and reference materials about common software vulnerabilities, including "
            "OWASP Top 10, CWE database entries, and Python-specific security issues. "
            "This tool is essential for understanding security context, explaining "
            "vulnerability impact, and identifying appropriate remediation strategies "
            "for vulnerabilities found in code analysis. "
            "The query should be a concise description of the security concern, "
            "vulnerability type, or code pattern being analyzed."
        ),
        rag_resources=[
            rag.RagResource(rag_corpus=vuln_rag_corpus)
        ],
        similarity_top_k=2,
        vector_distance_threshold=0.6,
    )


def get_safety_API_tool() -> MCPToolset:
    """Create a tool for scanning project dependencies using the Safety CLI API.

    The Safety API tool provides comprehensive dependency vulnerability scanning
    by checking project dependencies (from requirements.txt, pyproject.toml, etc.)
    against Safety's extensive database of known security vulnerabilities. This
    tool is essential for identifying vulnerable packages and understanding the
    security posture of third-party dependencies.

    Key Features:
    - Scans Python package dependencies for known CVE vulnerabilities
    - Provides detailed vulnerability information including severity ratings
    - Suggests specific package version updates to resolve security issues
    - Integrates with the comprehensive Safety CLI vulnerability database
    - Supports multiple dependency file formats (requirements.txt, Pipfile, etc.)
    - Provides actionable remediation recommendations

    The tool uses Model Context Protocol (MCP) over Server-Sent Events (SSE)
    to communicate with the Safety CLI service, enabling real-time vulnerability
    scanning and reporting.

    Returns:
        MCPToolset: Configured MCP toolset for Safety API access that provides
            dependency vulnerability scanning capabilities.

    Environment Variables:
        SAFETY_API_KEY (str): Bearer token for authenticating with the Safety CLI
            API service. Obtain this from https://safetycli.com/

    Raises:
        ValueError: If SAFETY_API_KEY environment variable is not set.
        ConnectionError: If unable to connect to Safety CLI service.
        AuthenticationError: If the provided API key is invalid.

    API Endpoint:
        - URL: https://mcp.safetycli.com/sse
        - Protocol: Server-Sent Events (SSE) over HTTPS
        - Authentication: Bearer token via Authorization header

    Example Usage:
        When scanning a requirements.txt file containing:
        ```
        django==2.0.0
        requests==2.20.0
        ```

        The tool might return:
        ```json
        {
            "vulnerabilities": [
                {
                    "package": "django",
                    "version": "2.0.0",
                    "vulnerability_id": "CVE-2023-12345",
                    "severity": "HIGH",
                    "description": "SQL injection vulnerability",
                    "fixed_versions": ["3.2.18", "4.1.7"]
                }
            ],
            "summary": {
                "total_vulnerabilities": 1,
                "high_severity": 1,
                "recommendations": "Update django to version 4.1.7 or later"
            }
        }
        ```

    Security Note:
        The Safety API key should be kept secure and not logged or exposed
        in error messages. Consider using secret management systems in
        production environments.
    """
    safety_api_key = os.environ.get("SAFETY_API_KEY", "").strip()
    if not safety_api_key:
        raise ValueError(
            "SAFETY_API_KEY environment variable is required for Safety API access. "
            "Please obtain an API key from https://safetycli.com/ and set the "
            "SAFETY_API_KEY environment variable."
        )


    return MCPToolset(
        connection_params=SseServerParams(
            url="https://mcp.safetycli.com/sse",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {safety_api_key}",
            },
        )
    )


def get_orchestrator_agent_tools() -> list:
    """
    Returns a list of AgentTool instances for the orchestrator agent.
    If USE_RAG environment variable is set, returns the search_agent wrapped in AgentTool.
    Otherwise, returns an empty list.

    Returns:
        List of AgentTool instances or empty list
    """
    if os.environ.get("USE_RAG"):
        search_agent = LlmAgent(
            name="SearchAgent",
            model=os.environ.get("LLM_DEPLOYMENT", "gemini-2.0-flash"),
            instruction=load_prompt("search_agent"),
            description="Searches for relevant cybersecurity vulnerability advise for mitigations.",
            output_key="search_report",
            tools=[get_rag_vulnerability_knowledge_tool()],
        )
        return [AgentTool(agent=search_agent)]
    return []

# Export public functions for use by agents
__all__ = [
    "get_rag_vulnerability_knowledge_tool",
    "get_safety_API_tool",
    "get_orchestrator_agent_tools",
]
