import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient

load_dotenv()

tavily_api_key = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=tavily_api_key)

websearch_config = {
    "parameter":{
        "default_num_results" : 3,
        "include_domains": []
    }
}

mcp = FastMCP(
    name="web_search",
    host="0.0.0.0",
    port=8006,
    instructions="Web search capability using Tavily API that provides real-time internet search results. Supports both basic and advanced search with filtering options including domain restrictions, text inclusion requirements, and date filtering. Returns formatted results with titles, URLs, publication dates, and content summaries."
)

@mcp.tool()
async def search_web(query:str, num_results:int = 3) -> str:
    """
    Performs real-time web search using the Tavily API.
    Returns latest search results in markdown format including titles, URLs, and content summaries.
    Use when you need current information, recent events, or data not available in your training.

    
    Parameters:
        query: Search query
        num_results: Number of results to return (default: 3)
    """

    try:
        search_args ={
            "max_results" : num_results or websearch_config['parameter']['default_num_results'],
            "search_depth" : "basic"
        }

        search_results = tavily_client.search(
            query=query,
            **search_args
        )

        return search_results
    
    except Exception as e:
        return f"Error occurred during Tavily search : {e}"

@mcp.resource("help: dev@brain-crew.com")
def get_search_help() -> str:
    """Provides help for web search tools."""

    return """
            # Web Search Tool Usage Guide
            
            Provides Claude with real-time web search capability through the Tavily API.
            
            ## Web Search
            The `search_web` tool performs simple web searches.
            - Parameters: 
            - query: Search query
            - num_results: Number of results to return (optional, default: 5)
            
            ## Examples
            - Web search: "I'm curious about the latest AI development trends"

            """

if __name__=="__main__":
    mcp.run(transport="stdio")