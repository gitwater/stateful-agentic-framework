"""
Long Term Memory (LTM) service for handling operations related to topic storage and retrieval.
"""

from ..models.ltm import Topic

class LongTermMemoryService:
    """
    Service class for long-term memory operations.
    Provides methods for storing and retrieving topics.
    """
    
    def __init__(self, db):
        """
        Initialize the LTM service.
        
        Args:
            db: The Database instance
        """
        self.db = db
    
    def store_topic_boundaries(self, user_id, agent_id, topic, topic_conversation_summary, 
                               start_utterance_id, end_utterance_id):
        """
        Store a new topic in long-term memory.
        
        Args:
            user_id (str): The user ID
            agent_id (str): The agent ID
            topic (str): The topic name
            topic_conversation_summary (str): The summary of the conversation about this topic
            start_utterance_id (str): The ID of the first utterance in this topic
            end_utterance_id (str): The ID of the last utterance in this topic
            
        Returns:
            Topic: The created Topic instance
        """
        with self.db.session() as session:
            topic = Topic.create(
                session=session,
                user_id=user_id,
                agent_id=agent_id,
                topic=topic,
                topic_conversation_summary=topic_conversation_summary,
                start_utterance_id=start_utterance_id,
                end_utterance_id=end_utterance_id
            )
            return topic
    
    def retrieve_topic_boundaries(self, user_id, agent_id, num_entries=10):
        """
        Retrieve topics from long-term memory.
        
        Args:
            user_id (str): The user ID
            agent_id (str): The agent ID
            num_entries (int): The number of entries to retrieve
            
        Returns:
            list: A list of dictionaries with topic information,
                 matching the format of the original implementation
        """
        with self.db.session() as session:
            topics = session.query(Topic)\
                .filter_by(user_id=user_id, agent_id=agent_id)\
                .order_by(Topic.created_at.desc())\
                .limit(num_entries)\
                .all()
            
            # Convert to dictionaries matching the original implementation's format
            return [{
                'topic': topic.topic,
                'start_utterance_id': topic.start_utterance_id,
                'end_utterance_id': topic.end_utterance_id
            } for topic in topics] 