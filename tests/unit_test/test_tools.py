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
"""Unit tests for security analysis tools module.

This module contains comprehensive unit tests for the tools.py module, covering RAG
vulnerability knowledge retrieval and Safety API integration. Tests include environment
variable validation, tool configuration, and error handling scenarios.
"""

import os
import pytest
from unittest.mock import MagicMock, Mock, patch

from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag

from app.tools import get_rag_vulnerability_knowledge_tool, get_safety_API_tool


class TestGetRagVulnerabilityKnowledgeTool:
    """Test suite for RAG vulnerability knowledge tool creation."""

    def test_get_rag_tool_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful creation of RAG vulnerability knowledge tool."""
        # Arrange
        test_corpus_id = "test-corpus-123"
        monkeypatch.setenv("VULN_RAG_CORPUS", test_corpus_id)

        with patch("app.tools.VertexAiRagRetrieval") as mock_rag_retrieval:
            mock_tool = Mock(spec=VertexAiRagRetrieval)
            mock_rag_retrieval.return_value = mock_tool

            # Act
            result = get_rag_vulnerability_knowledge_tool()

            # Assert
            assert result == mock_tool
            mock_rag_retrieval.assert_called_once_with(
                name="retrieve_vulnerability_knowledge",
                description=(
                    "Use this tool to retrieve comprehensive documentation, "
                    "best practices, and reference materials about common "
                    "software vulnerabilities, including OWASP Top 10, CWE "
                    "database entries, and Python-specific security issues. "
                    "This tool is essential for understanding security context, "
                    "explaining vulnerability impact, and identifying appropriate "
                    "remediation strategies for vulnerabilities found in code "
                    "analysis. The query should be a concise description of "
                    "the security concern, vulnerability type, or code pattern "
                    "being analyzed."
                ),
                rag_resources=[rag.RagResource(rag_corpus=test_corpus_id)],
                similarity_top_k=10,
                vector_distance_threshold=0.6,
            )

    def test_get_rag_tool_missing_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test RAG tool creation fails when environment variable is missing."""
        # Arrange
        monkeypatch.delenv("VULN_RAG_CORPUS", raising=False)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            get_rag_vulnerability_knowledge_tool()

        assert "VULN_RAG_CORPUS environment variable is required" in str(exc_info.value)
        assert "Vertex AI RAG corpus ID" in str(exc_info.value)

    def test_get_rag_tool_empty_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test RAG tool creation fails when environment variable is empty."""
        # Arrange
        monkeypatch.setenv("VULN_RAG_CORPUS", "")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            get_rag_vulnerability_knowledge_tool()

        assert "VULN_RAG_CORPUS environment variable is required" in str(exc_info.value)

    def test_get_rag_tool_none_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test RAG tool creation handles None environment variable."""
        # Arrange
        monkeypatch.delenv("VULN_RAG_CORPUS", raising=False)

        # Act & Assert
        with pytest.raises(ValueError):
            get_rag_vulnerability_knowledge_tool()

    @patch("app.tools.rag")
    def test_rag_resource_creation(
        self, mock_rag: Mock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that RAG resource is created with correct corpus ID."""
        # Arrange
        test_corpus_id = "projects/test/locations/us/ragCorpora/corpus-123"
        monkeypatch.setenv("VULN_RAG_CORPUS", test_corpus_id)

        mock_rag_resource = Mock()
        mock_rag.RagResource.return_value = mock_rag_resource

        with patch("app.tools.VertexAiRagRetrieval") as mock_rag_retrieval:
            # Act
            get_rag_vulnerability_knowledge_tool()

            # Assert
            mock_rag.RagResource.assert_called_once_with(rag_corpus=test_corpus_id)


class TestGetSafetyApiTool:
    """Test suite for Safety API tool creation."""

    def test_get_safety_tool_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful creation of Safety API tool."""
        # Arrange
        test_api_key = "sft_test_key_123456789"
        monkeypatch.setenv("SAFETY_API_KEY", test_api_key)

        with patch("app.tools.MCPToolset") as mock_mcp_toolset:
            mock_tool = Mock(spec=MCPToolset)
            mock_mcp_toolset.return_value = mock_tool

            # Act
            result = get_safety_API_tool()

            # Assert
            assert result == mock_tool
            mock_mcp_toolset.assert_called_once_with(
                connection_params=SseServerParams(
                    url="https://mcp.safetycli.com/sse",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {test_api_key}",
                    },
                )
            )

    def test_get_safety_tool_missing_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test Safety API tool creation fails when API key is missing."""
        # Arrange
        monkeypatch.delenv("SAFETY_API_KEY", raising=False)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            get_safety_API_tool()

        assert "SAFETY_API_KEY environment variable is required" in str(exc_info.value)
        assert "https://safetycli.com/" in str(exc_info.value)

    def test_get_safety_tool_empty_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test Safety API tool creation fails when API key is empty."""
        # Arrange
        monkeypatch.setenv("SAFETY_API_KEY", "")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            get_safety_API_tool()

        assert "SAFETY_API_KEY environment variable is required" in str(exc_info.value)

    def test_get_safety_tool_none_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test Safety API tool creation handles None environment variable."""
        # Arrange
        monkeypatch.delenv("SAFETY_API_KEY", raising=False)

        # Act & Assert
        with pytest.raises(ValueError):
            get_safety_API_tool()

    def test_safety_tool_correct_headers(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that Safety API tool is created with correct headers."""
        # Arrange
        test_api_key = "sft_production_key_abcdef123456"
        monkeypatch.setenv("SAFETY_API_KEY", test_api_key)

        with patch("app.tools.MCPToolset") as mock_mcp_toolset, \
             patch("app.tools.SseServerParams") as mock_sse_params:

            mock_params = Mock()
            mock_sse_params.return_value = mock_params

            # Act
            get_safety_API_tool()

            # Assert
            mock_sse_params.assert_called_once_with(
                url="https://mcp.safetycli.com/sse",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {test_api_key}",
                },
            )
            mock_mcp_toolset.assert_called_once_with(connection_params=mock_params)

    def test_safety_tool_bearer_token_format(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that API key is formatted correctly as Bearer token."""
        # Arrange
        test_api_key = "special-chars_123!@#"
        monkeypatch.setenv("SAFETY_API_KEY", test_api_key)

        with patch("app.tools.MCPToolset") as mock_mcp_toolset:
            # Act
            get_safety_API_tool()

            # Assert
            call_args = mock_mcp_toolset.call_args
            connection_params = call_args[1]["connection_params"]
            auth_header = connection_params.headers["Authorization"]

            assert auth_header == f"Bearer {test_api_key}"
            assert auth_header.startswith("Bearer ")


class TestToolsIntegration:
    """Integration tests for tools module functionality."""

    def test_both_tools_can_be_created_independently(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that both tools can be created without interfering."""
        # Arrange
        monkeypatch.setenv("VULN_RAG_CORPUS", "test-corpus")
        monkeypatch.setenv("SAFETY_API_KEY", "test-key")

        with patch("app.tools.VertexAiRagRetrieval") as mock_rag, \
             patch("app.tools.MCPToolset") as mock_safety:

            mock_rag_tool = Mock()
            mock_safety_tool = Mock()
            mock_rag.return_value = mock_rag_tool
            mock_safety.return_value = mock_safety_tool

            # Act
            rag_tool = get_rag_vulnerability_knowledge_tool()
            safety_tool = get_safety_API_tool()

            # Assert
            assert rag_tool == mock_rag_tool
            assert safety_tool == mock_safety_tool
            assert rag_tool != safety_tool

    def test_tools_module_exports(self) -> None:
        """Test that tools module exports expected functions."""
        from app import tools

        assert hasattr(tools, "get_rag_vulnerability_knowledge_tool")
        assert hasattr(tools, "get_safety_API_tool")
        assert hasattr(tools, "__all__")

        expected_exports = [
            "get_rag_vulnerability_knowledge_tool",
            "get_safety_API_tool",
        ]
        assert tools.__all__ == expected_exports

    def test_environment_isolation(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variables don't leak between tool creations."""
        # Arrange - Set only RAG env var
        monkeypatch.setenv("VULN_RAG_CORPUS", "test-corpus")
        monkeypatch.delenv("SAFETY_API_KEY", raising=False)

        # Act & Assert - RAG tool should work
        with patch("app.tools.VertexAiRagRetrieval"):
            get_rag_vulnerability_knowledge_tool()  # Should not raise

        # Act & Assert - Safety tool should fail
        with pytest.raises(ValueError):
            get_safety_API_tool()


class TestToolsErrorHandling:
    """Test error handling and edge cases for tools module."""

    def test_rag_tool_with_whitespace_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test RAG tool creation with whitespace-only environment variable."""
        # Arrange
        monkeypatch.setenv("VULN_RAG_CORPUS", "   ")

        # Act & Assert
        with pytest.raises(ValueError):
            get_rag_vulnerability_knowledge_tool()

    def test_safety_tool_with_whitespace_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test Safety tool creation with whitespace-only environment variable."""
        # Arrange
        monkeypatch.setenv("SAFETY_API_KEY", "   ")

        # Act & Assert
        with pytest.raises(ValueError):
            get_safety_API_tool()

    @patch("app.tools.logging_client")
    def test_logging_client_initialization(self, mock_logging_client: Mock) -> None:
        """Test that logging client is properly initialized."""
        # Import should trigger logging client creation
        from app import tools

        # The module should have initialized the logging client
        assert hasattr(tools, "logging_client")
        assert hasattr(tools, "logger")
