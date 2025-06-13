import os

from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag
from google.cloud import logging as google_cloud_logging


logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)

def get_rag_vulnerability_knowledge_tool() -> VertexAiRagRetrieval:
    """
    Returns the VertexAiRagRetrieval instance for vulnerability knowledge retrieval.
    """
    return VertexAiRagRetrieval(
        name="retrieve_vulnerability_knowledge",
        description=(
            "Use this tool to retrieve documentation, best practices, and reference materials "
            "about common software vulnerabilities, including OWASP Top 10, CWE Top, and "
            "Python-specific security issues. This is useful for understanding, explaining, "
            "or remediating vulnerabilities found in code."
            "The query should be a short explanation of the new code changes that are being made."
        ),
        rag_resources=[
            rag.RagResource(
                rag_corpus=os.environ.get(
                    "VULN_RAG_CORPUS"
                )  # Set this env var to your security corpus
            )
        ],
        similarity_top_k=10,
        vector_distance_threshold=0.6,
    )


def get_safety_API_tool() -> MCPToolset:
    """
    Returns the MCPToolset instance for the Safety API.
    The Safety API is used to scan new dependencies for vulnerabilities.
    """
    return MCPToolset(
        connection_params=SseServerParams(
            url="https://mcp.safetycli.com/sse",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ.get('SAFETY_API_KEY')}",
            },
        )
    )
