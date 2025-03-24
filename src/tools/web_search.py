"""
Web search tool implementation.
"""

import aiohttp
import json
import os
from typing import Dict, List, Any, Optional
from .tool_base import Tool
from openai import OpenAI



class WebSearchTool(Tool):
    """Tool for performing web searches using search APIs."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the web search tool.
        
        Args:
            api_key: API key for the search service.
                    If None, will try to get from environment variable.
        """
        super().__init__(
            name="WEB_SEARCH", 
            description="Search the web for information on a given query"
        )
        self.api_key = api_key or os.environ.get("SEARCH_API_KEY")
        if not self.api_key:
            self.logger.warning("No search API key provided. Some functionality may be limited.")
        
        # Define parameters for the tool
        self.parameters = {
            "query": {
                "type": "string",
                "description": "The search query to look up on the web"
            },
            "num_results": {
                "type": "integer",
                "description": "Number of search results to return (default: 5)"
            }
        }
        
        # Define which parameters are required
        self.required_parameters = ["query"]
    
    def get_prompt_description(self) -> str:
        """
        Get a detailed description of the web search tool for prompts.
        
        Returns:
            Formatted string describing the web search tool
        """
        return f"""{self.name}
  You are permitted to search the web for information relevant to your goals by using
  the following tool request phrase: @TOOL:{self.name}:[search query]
"""
            
    async def execute(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        Execute a web search.
        
        Args:
            query: The search query string
            num_results: Number of results to return (default: 5)
            
        Returns:
            Dict containing search results
        """

        client = OpenAI()

        completion = client.chat.completions.create(
            model="gpt-4o-search-preview",            
            messages=[{
                "role": "user",
                "content": query
            }]
        )

        return completion.choices[0].message.content
