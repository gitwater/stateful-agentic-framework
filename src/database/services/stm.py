"""
Short Term Memory (STM) service for handling operations related to conversation utterances.
"""

from sqlalchemy import desc
from ..models.stm import Utterance

class ShortTermMemoryService:
    """
    Service class for short-term memory operations.
    Provides methods for working with conversation utterances.
    """
    
    def __init__(self, db):
        """
        Initialize the STM service.
        
        Args:
            db: The Database instance
        """
        self.db = db
    
    def store_utterance(self, user_id, agent_id, speaker, utterance):
        """
        Store a new utterance.
        
        Args:
            user_id (str): The user ID
            agent_id (str): The agent ID
            speaker (str): The speaker (user, assistant, system, etc.)
            utterance (str): The utterance content
            
        Returns:
            Utterance: The created Utterance instance or None if duplicate
        """
        # Check for duplicates
        with self.db.session() as session:
            # Get the last utterance
            last_utterance = session.query(Utterance)\
                .filter_by(user_id=user_id, agent_id=agent_id)\
                .order_by(desc(Utterance.created_at))\
                .first()
                
            # If the last utterance is the same as the current utterance, don't store it
            if last_utterance and last_utterance.speaker == speaker and last_utterance.utterance == utterance:
                return None
                
            # Store the new utterance
            utterance_obj = Utterance.create(
                session=session,
                user_id=user_id,
                agent_id=agent_id,
                speaker=speaker,
                utterance=utterance
            )
            return utterance_obj
    
    def retrieve_utterances(self, user_id, agent_id, num_entries=-1):
        """
        Retrieve utterances.
        
        Args:
            user_id (str): The user ID
            agent_id (str): The agent ID
            num_entries (int): The number of utterances to retrieve (-1 for all)
            
        Returns:
            list: A list of dictionaries containing utterance information
        """
        with self.db.session() as session:
            # Build the query
            query = session.query(Utterance)\
                .filter_by(user_id=user_id, agent_id=agent_id)\
                .order_by(desc(Utterance.created_at))
                
            # Apply limit if specified
            if num_entries > 0:
                query = query.limit(num_entries)
                
            # Execute the query
            utterances = query.all()
            
            # Format the results
            entries_list = []
            for utterance in utterances:
                entries_list.append({
                    'id': utterance.id,
                    'speaker': utterance.speaker,
                    'utterance': utterance.utterance,
                    'created_at': utterance.created_at.isoformat() if utterance.created_at else None
                })
            return entries_list
    
    def retrieve_utterances_range(self, user_id, agent_id, start_id, end_id):
        """
        Retrieve utterances in a specific ID range.
        
        Args:
            user_id (str): The user ID
            agent_id (str): The agent ID
            start_id (int): The starting utterance ID
            end_id (int): The ending utterance ID
            
        Returns:
            list: A list of dictionaries containing utterance information
        """
        with self.db.session() as session:
            # Query utterances in the specified ID range
            utterances = session.query(Utterance)\
                .filter_by(user_id=user_id, agent_id=agent_id)\
                .filter(Utterance.id >= start_id, Utterance.id <= end_id)\
                .order_by(Utterance.created_at)\
                .all()
                
            # Format the results
            entries_list = []
            for utterance in utterances:
                entries_list.append({
                    'id': utterance.id,
                    'speaker': utterance.speaker,
                    'utterance': utterance.utterance,
                    'created_at': utterance.created_at.isoformat() if utterance.created_at else None
                })
            return entries_list
    
    def retrieve_utterances_since_id(self, user_id, agent_id, utterance_id):
        """
        Retrieve utterances after a specific ID.
        
        Args:
            user_id (str): The user ID
            agent_id (str): The agent ID
            utterance_id (int): The ID to retrieve utterances after
            
        Returns:
            list: A list of dictionaries containing utterance information
        """
        with self.db.session() as session:
            # Query utterances since the specified ID
            utterances = session.query(Utterance)\
                .filter_by(user_id=user_id, agent_id=agent_id)\
                .filter(Utterance.id > utterance_id)\
                .order_by(Utterance.created_at)\
                .all()
                
            # Format the results
            entries_list = []
            for utterance in utterances:
                entries_list.append({
                    'id': utterance.id,
                    'speaker': utterance.speaker,
                    'utterance': utterance.utterance,
                    'created_at': utterance.created_at.isoformat() if utterance.created_at else None
                })
            return entries_list 