"""
Agents service for handling operations related to agent configuration and metadata.
"""

import yaml
from ..models.agents import Agent
from sqlalchemy import and_

class AgentsService:
    """
    Service class for agent operations.
    Provides methods for creating, updating, retrieving, and deleting agents.
    """
    
    def __init__(self, db):
        """
        Initialize the Agents service.
        
        Args:
            db: The Database instance
        """
        self.db = db
    
    def create_agent(self, user_id, agent_id, config):
        """
        Create a new agent for a user.
        
        Args:
            user_id (str): The user ID
            agent_id (str): The agent ID
            config (str): The YAML configuration string
            
        Returns:
            Agent: The created Agent instance
        """
        with self.db.session() as session:
            agent = Agent.create(
                session=session,
                user_id=user_id,
                agent_id=agent_id,
                config=config
            )
            
            session.commit()
            return agent
    
    def get_agent(self, user_id, agent_id):
        """
        Get an agent by user_id and agent_id.
        
        Args:
            user_id (str): The user ID
            agent_id (str): The agent ID
            
        Returns:
            dict: Dictionary with agent data if found, None otherwise
        """
        with self.db.session() as session:
            agent = session.query(Agent).filter(
                and_(
                    Agent.user_id == user_id,
                    Agent.agent_id == agent_id
                )
            ).first()
            
            if agent:
                # Extract data within the session
                return {
                    "agent_id": agent.agent_id,
                    "user_id": agent.user_id,
                    "config": agent.config
                }
            
            return None
    
    def list_agents(self, user_id):
        """
        List all agents for a user.
        
        Args:
            user_id (str): The user ID
            
        Returns:
            list: List of dictionaries containing agent data
        """
        with self.db.session() as session:
            agents = session.query(Agent).filter(
                Agent.user_id == user_id
            ).all()
            
            # Extract all necessary data within the session
            agent_data = []
            for agent in agents:
                agent_data.append({
                    "agent_id": agent.agent_id,
                    "user_id": agent.user_id,
                    "config": agent.config
                })
            
            return agent_data
    
    def update_agent(self, user_id, agent_id, config):
        """
        Update an existing agent's configuration.
        
        Args:
            user_id (str): The user ID
            agent_id (str): The agent ID
            config (str): The updated YAML configuration string
            
        Returns:
            dict: Dictionary with the updated agent data if found, None otherwise
        """
        with self.db.session() as session:
            agent = session.query(Agent).filter(
                and_(
                    Agent.user_id == user_id,
                    Agent.agent_id == agent_id
                )
            ).first()
            
            if agent:
                agent.config = config
                session.commit()
                # Extract data within the session
                return {
                    "agent_id": agent.agent_id,
                    "user_id": agent.user_id,
                    "config": agent.config
                }
                
            return None
    
    def delete_agent(self, user_id, agent_id):
        """
        Delete an agent.
        
        Args:
            user_id (str): The user ID
            agent_id (str): The agent ID
            
        Returns:
            bool: True if agent was deleted, False otherwise
        """
        with self.db.session() as session:
            agent = session.query(Agent).filter(
                and_(
                    Agent.user_id == user_id,
                    Agent.agent_id == agent_id
                )
            ).first()
            
            if agent:
                session.delete(agent)
                session.commit()
                return True
                
            return False
    
    def extract_metadata(self, config_yaml):
        """
        Extract metadata from agent config YAML.
        Public method for external use.
        
        Args:
            config_yaml (str): The YAML configuration string
            
        Returns:
            dict: Dictionary with name, description, and purpose fields
        """
        try:
            config = yaml.safe_load(config_yaml)
            return {
                "name": config.get("name", "Unnamed Agent"),
                "description": config.get("description", ""),
                "purpose": config.get("purpose", "")
            }
        except Exception:
            return {
                "name": "Unnamed Agent",
                "description": "",
                "purpose": ""
            } 