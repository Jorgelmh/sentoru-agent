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
            "The query should be a short general explanation of the new code changes that are being introduced, as well as identified vulnerabilities."
        ),
        rag_resources=[
            rag.RagResource(
                rag_corpus=os.environ.get(
                    "VULN_RAG_CORPUS",
                )  # Set this env var to your security corpus
            )
        ],
        similarity_top_k=2,
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
