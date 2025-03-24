"""
Example of how to use the tools layer.
"""

import asyncio
import logging
from .tools_manager import ToolsManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def run_example():
    """Run an example of using the tools layer."""
    
    # Initialize the tools manager
    tools_manager = ToolsManager()
    
    # Show available tools
    print("Available tools:")
    for tool in tools_manager.get_all_tools():
        print(f"- {tool.name}: {tool.description}")
    
    # Example: Perform a web search
    print("\nPerforming a web search...")
    search_results = await tools_manager.execute_tool(
        "web_search", 
        query="latest developments in AI"
    )
    
    # Display results
    if search_results.get("success", False):
        print(f"Search results for: {search_results['query']}")
        for i, result in enumerate(search_results["results"], 1):
            print(f"\n{i}. {result['title']}")
            print(f"   {result['link']}")
            print(f"   {result['snippet']}")
    else:
        print(f"Search failed: {search_results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    # Run the async example
    asyncio.run(run_example()) 