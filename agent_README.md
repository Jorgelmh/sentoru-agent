# Sentoru Agent Repository Guide

<img src="docs/resources/sentoru-logo.png" alt="Sentoru Logo" width="200">

A comprehensive guide to the **Sentoru** repository structure and architecture for AI agents. Sentoru is a hierarchical multi-agent security system built with Google's Agent Development Kit (ADK) that provides automated security analysis, vulnerability fixing, and penetration testing for code repositories.

## 🏗️ Repository Architecture

### Core Application Structure

```
app/
├── agent.py                 # Root orchestrator agent entry point
├── agent_engine_app.py      # ADK engine application wrapper
├── agents/                  # Specialized security agents
│   ├── analyst_agent.py     # Security vulnerability analysis
│   ├── fixer_agent.py       # Automated vulnerability patching
│   └── pentester_agent.py   # Penetration testing validation
├── prompts/                 # Agent instruction templates
│   ├── orchestrator_agent.md # Master coordinator instructions
│   ├── search_agent.md      # RAG knowledge retrieval instructions
│   ├── analyst_agent.md     # Security analysis instructions
│   ├── fixer_agent.md       # Vulnerability fixing instructions
│   └── pentester_agent.md   # Penetration testing instructions
├── tools.py                 # Agent tools and utilities
└── utils/                   # Supporting utilities
    ├── gcs.py              # Google Cloud Storage operations
    ├── tracing.py          # Observability and logging
    ├── typing.py           # Type definitions
    └── util.py             # Common utility functions
```

### Multi-Agent System Hierarchy

**Sentoru implements a sophisticated hierarchical multi-agent architecture:**

1. **Orchestrator Agent** (`app/agent.py: root_agent`)
   - Master coordinator managing the entire security workflow
   - Conditionally invokes Search Agent based on `USE_RAG` configuration
   - Delegates to Review Agent for sequential security analysis

2. **Search Agent** (`app/tools.py: get_search_agent()`)
   - Optional RAG-powered knowledge retrieval agent
   - Queries Vertex AI RAG corpus for security best practices
   - Provides contextual intelligence from OWASP, CWE, and security sources

3. **Review Agent** (`app/agent.py: review_agent`)
   - Sequential pipeline of three specialized security agents:
     - **Analyst Agent**: Identifies security vulnerabilities
     - **Fixer Agent**: Generates patches for vulnerabilities  
     - **Pentester Agent**: Creates tests to validate fixes

### Tools and Capabilities

**Security Analysis Tools:**
- `get_rag_vulnerability_knowledge_tool()`: RAG-based security knowledge retrieval
- `get_safety_API_tool()`: Dependency vulnerability scanning
- `get_orchestrator_agent_tools()`: Conditional tool provisioning

**Supported Operations:**
- Git diff analysis and security assessment
- Automated vulnerability patching in GitHub format
- Penetration test generation using pytest framework
- RAG-enhanced security context gathering

## 🧪 Examples and Testing

### Integration Tests Location

Find practical examples in `tests/integration/`:

```
tests/
├── integration/
│   └── test_agent.py        # End-to-end agent workflow tests
├── samples/                 # Sample git diffs for testing
│   ├── sample.diff         # Example with vulnerabilities
│   └── sample_clean.diff   # Clean code example
└── unit/
    └── test_utils.py       # Utility function tests
```

### Jupyter Notebooks for Interactive Testing

```
notebooks/
├── adk_app_testing.ipynb       # Interactive agent testing
└── evaluating_adk_agent.ipynb # Agent evaluation workflows
```

**Key Testing Patterns:**
- Load sample git diffs from `tests/samples/`
- Initialize agent with proper session state
- Execute full security analysis workflow
- Validate JSON response format and security findings

### Example Usage Pattern

```python
# Initialize agent with git diff context
agent_state = {"git_diff": load_sample_diff()}

# Execute security workflow
response = root_agent.execute(
    query="Analyze this code for security vulnerabilities",
    state=agent_state
)

# Extract results
analysis = response.get("analysis")
fixes = response.get("fixed_code_patches") 
tests = response.get("test_code")
```

## 🛠️ Configuration and Environment

### Required Environment Variables

```bash
GOOGLE_CLOUD_PROJECT=<your-project-id>
GOOGLE_GENAI_USE_VERTEXAI=True
GOOGLE_CLOUD_LOCATION=us-central1
LLM_DEPLOYMENT=gemini-2.0-flash
SAFETY_API_KEY=<safety-api-key>
VULN_RAG_CORPUS=<rag-corpus-resource-name>  # For RAG capabilities
USE_RAG=true                                # Toggle RAG functionality
```

### Deployment Considerations

- **Local Development**: Full RAG capabilities available
- **Cloud Deployment**: RAG must be disabled (`USE_RAG` unset) due to ADK limitation
- **GitHub Integration**: Automated PR analysis via webhook triggers

## 🔍 Key Implementation Details

### Agent State Management
- Git diff context passed through `before_agent_callback`
- Session state maintains security analysis context
- Structured JSON responses for downstream processing

### Security Knowledge Base
- Vertex AI RAG corpus with OWASP, CWE, security documents
- Generated using Gemini Deep Research capabilities
- Vectorized with `text-embedding-005` for semantic search

### Tool Integration Patterns
- Agent-as-a-Tool pattern for Search Agent
- Conditional tool provisioning based on configuration
- MCP toolset integration for external security APIs

## 📚 Additional Resources

- **ADK Documentation**: [https://google.github.io/adk-docs/](https://google.github.io/adk-docs/)
- **Repository**: [GitHub - Sentoru Agent](https://github.com/your-org/sentoku-agent)
- **Demo Video**: [YouTube Demo](https://www.youtube.com/watch?v=w-aS35DFAQo)
- **GitHub App**: [Install Sentoru](https://github.com/apps/sentoru-ai)
