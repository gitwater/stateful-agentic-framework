
class SQLDatabaseLTM:
    def __init__(self, conn):
        self.conn = conn

    def create_tables(self):
        # Long Term Memory State
        cursor = self.conn.cursor()
        if 1 == 0:
            # Drop the table
            cursor.execute('''
                DROP TABLE IF EXISTS ltm_topics
            ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ltm_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                topic_converstation_summary TEXT NOT NULL,
                start_utterance_id TEXT NOT NULL,
                end_utterance_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

   # LTM: Topic Boundaries
    def store_topic_boundaries(self, topic, topic_converstation_summary, start_utterance_id, end_utterance_id):
        cursor = self.conn.cursor()
        cursor.execute(f'''
            INSERT INTO ltm_topics (topic, topic_converstation_summary, start_utterance_id, end_utterance_id)
            VALUES ("{topic}", "{topic_converstation_summary}", {start_utterance_id}, {end_utterance_id})''')
        self.conn.commit()

    def retreive_topic_boundaries(self, num_entries=10):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM ltm_topics
            ORDER BY created_at DESC
            LIMIT ?
        ''', (num_entries,))
        entries = cursor.fetchall()
        # convert entries into a list of dictionaries
        entries_list = []
        for entry in entries:
            entries_list.append({
                'topic': entry[1],
                'start_utterance_id': entry[2],
                'end_utterance_id': entry[3]
            })
        return entries_list
