"""
Core database module that provides the main Database class and SQLAlchemy configuration.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
import utils

# Create the declarative base that will be used for all models
Base = declarative_base()

class Database:
    """
    Main database class that manages the connection to the database and provides
    access to the various database services (auth, LTM, STM, states).
    
    This class uses a shared table approach instead of separate databases for each user/agent.
    """
    
    def __init__(self, system_container="main", db_url=None):
        """
        Initialize the database connection.
        
        Args:
            system_container (str): The system container name, used for database naming
            db_url (str, optional): Database URL. If None, will use SQLite with the system_container name
        """
        self.system_container = utils.normalize_folder_name(system_container)
        
        # If no db_url is provided, use SQLite with the system container name
        if db_url is None:
            # Create the database directory if it doesn't exist
            db_dir = f"db/{self.system_container}"
            os.makedirs(db_dir, exist_ok=True)
            db_url = f"sqlite:///{db_dir}/database.db"
        
        self.engine = create_engine(db_url, echo=False)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
        
        # Initialize database components
        from .services.ltm import LongTermMemoryService
        from .services.stm import ShortTermMemoryService
        from .services.states import StatesService
        from .services.agents import AgentsService
        
        self.ltm = LongTermMemoryService(self)
        self.stm = ShortTermMemoryService(self)
        self.states = StatesService(self)
        self.agents = AgentsService(self)
        
        # Auto-create tables if they don't exist
        self.create_all()
    
    def create_all(self):
        """Create all tables defined in the models."""
        from .models import all_models  # This import is just to ensure all models are loaded
        Base.metadata.create_all(self.engine)
    
    @contextmanager
    def session(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session(self):
        """Get a new session."""
        return self.Session()
    
    def dispose(self):
        """Dispose of the engine and all sessions."""
        self.Session.remove()
        self.engine.dispose() 