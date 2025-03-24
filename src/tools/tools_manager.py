"""
Tools manager to handle and execute tools.
"""

import logging
from typing import Dict, List, Any, Optional, Type
from .tool_base import Tool
from .web_search import WebSearchTool

class ToolsManager:
    """
    Manager for handling all available tools.
    Provides a centralized interface for tool registration and execution.
    """
    
    def __init__(self):
        """Initialize the tools manager with available tools."""
        self.logger = logging.getLogger("tools.manager")
        self.available_tools: Dict[str, Tool] = {}
        
        # Register built-in tools
        self._register_default_tools()
        
    def _register_default_tools(self):
        """Register the default built-in tools."""
        self.register_tool(WebSearchTool())
        
    def register_tool(self, tool: Tool) -> None:
        """
        Register a new tool with the manager.
        
        Args:
            tool: A Tool instance to register
        """
        self.available_tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")
        
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """
        Get a tool by name.
        
        Args:
            tool_name: Name of the tool to retrieve
            
        Returns:
            Tool instance if found, None otherwise
        """
        return self.available_tools.get(tool_name)
        
    def get_all_tools(self) -> List[Tool]:
        """
        Get all registered tools.
        
        Returns:
            List of all registered Tool instances
        """
        return list(self.available_tools.values())
    
    def get_tool_descriptions(self) -> List[Dict[str, str]]:
        """
        Get metadata for all registered tools.
        
        Returns:
            List of tool metadata dictionaries
        """
        return [tool.get_metadata() for tool in self.available_tools.values()]
    
    def get_tools_prompt_description(self) -> str:
        """
        Generate a formatted string describing all available tools for inclusion in prompts.
        
        Returns:
            Formatted string with tool descriptions and usage instructions
        """
        if not self.available_tools:
            return ""
            
        tools_desc = """
AVAILABLE TOOLS: START
"""
        
        # Get description from each tool
        for tool in self.available_tools.values():
            tools_desc += tool.get_prompt_description()
            
        tools_desc += """
TOOL WORKFLOW:
  - Your tool requests will be processed automatically and not shown to the user.
  - You will receive the tool results in a follow-up interaction.
AVAILABLE TOOLS: END
"""
        
        return tools_desc
        
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Arguments to pass to the tool execution
            
        Returns:
            Dict containing the results of the tool execution
            
        Raises:
            ValueError: If the tool doesn't exist
        """
        tool = self.get_tool(tool_name)
        if tool is None:
            error_msg = f"Tool not found: {tool_name}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
        self.logger.info(f"Executing tool: {tool_name}")
        try:
            result = await tool.execute(**kwargs)
            return result
        except Exception as e:
            self.logger.exception(f"Error executing tool {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": f"Tool execution error: {str(e)}"
            }
            
    def parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse a potential tool call from the agent's response text.
        
        Args:
            text: The text to parse for tool calls
            
        Returns:
            Dict with tool_name and parameters if a tool call is found, None otherwise
        """
        import re
        import json
        
        # Pattern to match the new tool call format (without tags)
        pattern = r"tool:\s*(\w+)\s*params:\s*({.*?})"
        match = re.search(pattern, text, re.DOTALL)
        
        if match:
            tool_name = match.group(1).strip()
            try:
                params_json = match.group(2).strip()
                parameters = json.loads(params_json)
                return {
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "full_match": match.group(0)  # Return the full matched text for replacement
                }
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse tool parameters: {e}")
                return None
        
        return None
        
    def extract_all_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract all tool calls from the agent's response text.
        
        Args:
            text: The text to parse for tool calls
            
        Returns:
            List of dicts with tool_name, parameters, and the full match for each tool call
        """
        import re
        import json
        
        # Pattern to match all tool calls (without tags)
        pattern = r"tool:\s*(\w+)\s*params:\s*({.*?})"
        matches = re.finditer(pattern, text, re.DOTALL)
        
        tool_calls = []
        for match in matches:
            tool_name = match.group(1).strip()
            try:
                params_json = match.group(2).strip()
                parameters = json.loads(params_json)
                tool_calls.append({
                    "tool_name": tool_name.upper(),
                    "parameters": parameters,
                    "full_match": match.group(0),
                    "match_span": match.span()
                })
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse tool parameters: {e}")
                
        return tool_calls 