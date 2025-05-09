from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from utils.model import load_openai_model

from langchain_tools.get_weather import get_weather

model = load_openai_model()


@asynccontextmanager
async def make_graph():
    async with MultiServerMCPClient(
        {
            "Retriever" : {
                "command": "python",
                "args": ["./mcp_tools/rag/mcp_server_rag.py"],
                "transport": "stdio"
            },
            "notion-api" : {
                "command": "python",
                "args": ["-m", "notion_api_mcp"],
                "transport": "stdio"
            },
            "web_search" : {
                "command":"python",
                "args": ["./mcp_tools/web_search/mcp_server_web_search.py"],
                "transport": "stdio"
            },
        }
    ) as client:
        tools = client.get_tools()
        tools.append(get_weather)
        agent = create_react_agent(model, tools)
        yield agent