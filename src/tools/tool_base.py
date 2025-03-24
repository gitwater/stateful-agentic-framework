"""
Base class for all tools in the tools layer.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional

class Tool(ABC):
    """Base abstract class for all tools."""

    def __init__(self, name: str, description: str):
        """
        Initialize a tool.
        
        Args:
            name: The name of the tool
            description: A brief description of what the tool does
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"tools.{name}")

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool's functionality.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Dict containing the results of the tool execution
        """
        pass

    def get_metadata(self) -> Dict[str, str]:
        """
        Get tool metadata for function calling/tools APIs.
        
        Returns:
            Dict containing name and description
        """
        return {
            "name": self.name,
            "description": self.description
        }
        
    def get_prompt_description(self) -> str:
        """
        Get the detailed description of the tool for inclusion in LLM prompts.
        
        Returns:
            Formatted string describing the tool's purpose, parameters, and usage
        """
        metadata = self.get_metadata()
        tool_name = metadata['name']
        
        # Generic implementation that can be overridden by specific tools
        description = f"TOOL: {tool_name}\n"
        description += f"DESCRIPTION: {metadata['description']}\n\n"
        
        # Add parameter information if available
        if hasattr(self, 'parameters'):
            description += "PARAMETERS:\n\n"
            for param_name, param_info in self.parameters.items():
                required = "required" if param_name in getattr(self, 'required_parameters', []) else "optional"
                param_type = param_info.get('type', 'any')
                param_desc = param_info.get('description', '')
                default = param_info.get('default', '')
                
                if default:
                    description += f"{param_name} ({param_type}, {required}, default={default}): {param_desc}\n\n"
                else:
                    description += f"{param_name} ({param_type}, {required}): {param_desc}\n\n"
        
        # Add when to use and when not to use sections
        description += "WHEN TO USE:\n\n"
        description += f"You're uncertain or guessing\n\n"
        description += f"User explicitly asks for {tool_name}\n\n"
        
        description += "WHEN NOT TO USE:\n\n"
        description += "Information confidently known\n\n"
        description += "General knowledge already covered by training data\n\n"
        
        return description 