# Database Layer

This directory contains the ORM database layer for the application. It uses SQLAlchemy for ORM and Alembic for migrations.

## Structure

- `core.py`: Main Database class that initializes the connection and provides access to services
- `models/`: SQLAlchemy models for the database tables
  - `base.py`: Base model classes and mixins
  - `ltm.py`: Long-term memory models
  - `stm.py`: Short-term memory models
  - `states.py`: Persona state models
- `services/`: Business logic for interacting with the database
  - `ltm.py`: Long-term memory services
  - `stm.py`: Short-term memory services
  - `states.py`: Persona state services
- `migrations/`: Alembic migration configuration and scripts
- `vector_store.py`: Vector database interface for storing and querying embeddings

## Usage

```python
from database import Database

# Initialize the database
db = Database()

# Create all tables
db.create_all()

# Use LTM service
topic = db.ltm.store_topic_boundaries(
    user_id="user123",
    agent_id="agent456",
    topic="Python Programming",
    topic_conversation_summary="Discussed Python basics and advanced concepts",
    start_utterance_id="msg1",
    end_utterance_id="msg10"
)

# Use STM service
conversation = db.stm.create_conversation(
    user_id="user123",
    agent_id="agent456",
    title="Python Discussion"
)

message = db.stm.add_message(
    user_id="user123",
    agent_id="agent456",
    conversation_id=conversation.id,
    role="user",
    content="Hello, can you teach me Python?"
)

# Use States service
db.states.set_persona_current_state(
    user_id="user123",
    agent_id="agent456",
    state={"mood": "happy", "topic": "Python"}
)
```

## Migrations

To generate a new migration:

```bash
cd src
alembic -c database/migrations/alembic.ini revision --autogenerate -m "Description of change"
```

To apply migrations:

```bash
cd src
alembic -c database/migrations/alembic.ini upgrade head
```

## Vector Database

The vector database interface supports ChromaDB and will support PostgreSQL in the future:

```python
from database.vector_store import VectorStore

# Initialize the vector store
vector_store = VectorStore(
    user_id="user123",
    agent_id="agent456",
    db_type="chroma",  # or "postgres" in the future
    collection_name="knowledge"
)

# Add documents
vector_store.add(
    texts=["Python is a programming language", "SQLAlchemy is an ORM for Python"],
    metadata=[{"source": "documentation"}, {"source": "tutorial"}]
)

# Query documents
results = vector_store.query(
    query_text="Tell me about Python",
    n_results=5
)
``` 