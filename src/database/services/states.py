"""
States service for handling operations related to persona states.
"""

import json
from ..models.states import PersonaState

class StatesService:
    """
    Service class for persona state operations.
    Provides methods for storing and retrieving persona states.
    """
    
    def __init__(self, db):
        """
        Initialize the States service.
        
        Args:
            db: The Database instance
        """
        self.db = db
    
    def set_persona_state_data(self, user_id, agent_id, state_name, state_data):
        """
        Set state data for a persona.
        
        Args:
            user_id (str): The user ID
            agent_id (str): The agent ID
            state_name (str): The name of the state
            state_data (any): The state data (will be JSON serialized)
            
        Returns:
            PersonaState: The created or updated PersonaState instance
        """
        # Serialize the state data
        state_data_json = json.dumps(state_data)
        
        with self.db.session() as session:
            # Check if state with this name already exists
            existing = session.query(PersonaState)\
                .filter_by(user_id=user_id, agent_id=agent_id, name=state_name)\
                .first()
                
            if existing:
                existing.state_data = state_data_json
                session.flush()
                return existing
                
            state = PersonaState.create(
                session=session,
                user_id=user_id,
                agent_id=agent_id,
                name=state_name,
                state_data=state_data_json
            )
            return state
    
    def get_persona_state_data(self, user_id, agent_id, state_name):
        """
        Get state data for a persona.
        
        Args:
            user_id (str): The user ID
            agent_id (str): The agent ID
            state_name (str): The name of the state
            
        Returns:
            any: The state data (deserialized from JSON) or None if not found
        """
        with self.db.session() as session:
            state = session.query(PersonaState)\
                .filter_by(user_id=user_id, agent_id=agent_id, name=state_name)\
                .first()
                
            if not state:
                return None
                
            return json.loads(state.state_data)
    
    def set_persona_current_state(self, user_id, agent_id, state):
        """
        Set the current state for a persona.
        This is a convenience method that calls set_persona_state_data with the name 'current_state'.
        
        Args:
            user_id (str): The user ID
            agent_id (str): The agent ID
            state (any): The state data
            
        Returns:
            PersonaState: The created or updated PersonaState instance
        """
        return self.set_persona_state_data(user_id, agent_id, 'current_state', state)
    
    def get_persona_current_state(self, user_id, agent_id):
        """
        Get the current state for a persona.
        This is a convenience method that calls get_persona_state_data with the name 'current_state'.
        
        Args:
            user_id (str): The user ID
            agent_id (str): The agent ID
            
        Returns:
            any: The state data or None if not found
        """
        return self.get_persona_state_data(user_id, agent_id, 'current_state') 

    def delete_persona_states(self, user_id, agent_id):
        """
        Delete all persona states for a given user and agent.
        """
        with self.db.session() as session:
            session.query(PersonaState).filter_by(user_id=user_id, agent_id=agent_id).delete()

        return True
