"""
Vector database interface for storing and querying vector embeddings.
Currently supports ChromaDB and will support PostgreSQL in the future.
"""

import os
import json

class VectorStore:
    """
    Vector database interface that abstracts away the specific vector database implementation.
    Currently supports ChromaDB and will support PostgreSQL in the future.
    """
    
    def __init__(self, user_id, agent_id, db_type="chroma", collection_name="default", db_url=None):
        """
        Initialize the vector database connection.
        
        Args:
            user_id (str): The user ID
            agent_id (str): The agent ID
            db_type (str): The database type ("chroma" or "postgres")
            collection_name (str): The collection name to use
            db_url (str, optional): Database URL for PostgreSQL
        """
        self.user_id = user_id
        self.agent_id = agent_id
        self.db_type = db_type
        
        # Generate a ChromaDB-compatible collection name
        self.collection_name = self._create_valid_collection_name(user_id, agent_id, collection_name)
        
        self.client = None
        self.collection = None
        
        if db_type == "chroma":
            self._init_chroma()
        elif db_type == "postgres":
            self._init_postgres(db_url)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def _create_valid_collection_name(self, user_id, agent_id, collection_name):
        """
        Create a valid ChromaDB collection name from user_id, agent_id, and collection_name.
        
        ChromaDB requirements:
        1. 3-63 characters long
        2. Start and end with alphanumeric characters
        3. Otherwise only alphanumeric, underscore, hyphen
        4. No consecutive periods
        5. Not a valid IPv4 address
        
        Args:
            user_id (str): The user ID
            agent_id (str): The agent ID
            collection_name (str): The base collection name
            
        Returns:
            str: A valid ChromaDB collection name
        """
        import hashlib
        import re
        
        # Create short hashes of the IDs
        user_hash = hashlib.md5(user_id.encode()).hexdigest()[:6]
        agent_hash = hashlib.md5(agent_id.encode()).hexdigest()[:6]
        
        # Create base name (ensure it starts with a letter to avoid potential IP-like names)
        base_name = f"c_{user_hash}_{agent_hash}_{collection_name}"
        
        # Remove invalid characters (keep only alphanumeric, underscore, hyphen)
        clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', base_name)
        
        # Ensure it doesn't have consecutive periods (shouldn't happen after above cleaning)
        clean_name = re.sub(r'\.{2,}', '_', clean_name)
        
        # Ensure it starts and ends with alphanumeric
        if not clean_name[0].isalnum():
            clean_name = 'c' + clean_name[1:]
        if not clean_name[-1].isalnum():
            clean_name = clean_name[:-1] + '0'
        
        # Ensure length is between 3 and 63 characters
        if len(clean_name) < 3:
            clean_name = clean_name + '000'
        if len(clean_name) > 63:
            clean_name = clean_name[:63]
            # Ensure it still ends with alphanumeric after truncation
            if not clean_name[-1].isalnum():
                clean_name = clean_name[:-1] + '0'
            
        return clean_name
    
    def _init_chroma(self):
        """Initialize ChromaDB client and collection."""
        import chromadb
        from chromadb.config import Settings
        
        # Create directory for ChromaDB persistence
        persist_directory = f"db/vector/chroma/{self.user_id}_{self.agent_id}"
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
    
    def _init_postgres(self, db_url):
        """
        Initialize PostgreSQL vector database client and collection.
        This will be implemented in the future.
        
        Args:
            db_url (str): PostgreSQL database URL
        """
        # Placeholder for future PostgreSQL implementation
        # Will use pgvector extension when implemented
        raise NotImplementedError("PostgreSQL vector database support not yet implemented")
    
    def add(self, texts, metadata=None, ids=None):
        """
        Add text documents to the vector database.
        
        Args:
            texts (list): List of text documents to embed and store
            metadata (list, optional): List of metadata dictionaries for each document
            ids (list, optional): List of IDs for each document
            
        Returns:
            list: List of IDs for the added documents
        """
        # If metadata or ids are None, create empty lists
        if metadata is None:
            metadata = [{} for _ in texts]
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(texts))]
        
        # Add user_id and agent_id to metadata
        for meta in metadata:
            meta["user_id"] = self.user_id
            meta["agent_id"] = self.agent_id
        
        if self.db_type == "chroma":
            self.collection.add(
                documents=texts,
                metadatas=metadata,
                ids=ids
            )
        elif self.db_type == "postgres":
            # Placeholder for future PostgreSQL implementation
            pass
        
        return ids
    
    def query(self, query_text, n_results=5, where=None):
        """
        Query the vector database for similar documents.
        
        Args:
            query_text (str): The query text
            n_results (int): The number of results to return
            where (dict, optional): Filter condition for metadata
            
        Returns:
            list: List of search results with document text, metadata, and score
        """
        # Ensure where filter includes user_id and agent_id
        if where is None:
            where = {}
        where["user_id"] = self.user_id
        where["agent_id"] = self.agent_id
        
        if self.db_type == "chroma":
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "id": results["ids"][0][i],
                    "score": results["distances"][0][i] if "distances" in results else None
                })
            
            return formatted_results
        elif self.db_type == "postgres":
            # Placeholder for future PostgreSQL implementation
            return []
    
    def delete(self, ids=None, where=None):
        """
        Delete documents from the vector database.
        
        Args:
            ids (list, optional): List of document IDs to delete
            where (dict, optional): Filter condition for metadata
            
        Returns:
            bool: True if successful
        """
        # Ensure where filter includes user_id and agent_id
        if where is None:
            where = {}
        where["user_id"] = self.user_id
        where["agent_id"] = self.agent_id
        
        if self.db_type == "chroma":
            if ids is not None:
                self.collection.delete(ids=ids)
            elif where is not None:
                self.collection.delete(where=where)
        elif self.db_type == "postgres":
            # Placeholder for future PostgreSQL implementation
            pass
        
        return True 