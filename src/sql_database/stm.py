
class SQLDatabaseSTM:
    def __init__(self, conn):
        self.conn = conn

    def create_tables(self):
        # Long Term Memory State
        cursor = self.conn.cursor()
        if 1 == 0:
            # Drop the table
            cursor.execute('''
                DROP TABLE IF EXISTS utterances
            ''')
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS utterances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                speaker TEXT NOT NULL,
                utterance TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    # -------------------------------------------------------------------------------
    # Utterances
    def store_utterance(self, speaker, utterance):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO utterances (speaker, utterance)
            VALUES (?, ?)
        ''', (speaker, utterance))
        self.conn.commit()

    def retreive_utterances(self, num_entries=-1):
        cursor = self.conn.cursor()
        # if num_entries is -1, return all entries
        if num_entries <= 0:
            cursor.execute('''
                SELECT * FROM utterances
                ORDER BY created_at ASC
            ''')
        else:
            cursor.execute('''
                SELECT * FROM utterances
                ORDER BY created_at ASC
                LIMIT ?
            ''', (num_entries,))
        entries = cursor.fetchall()
        # convert entries into a list of dictionaries
        entries_list = []
        for entry in entries:
            entries_list.append({
                'id': entry[0],
                'speaker': entry[1],
                'utterance': entry[2],
                'created_at': entry[3]
            })
        return entries_list

    # Return a range of utterances between start_id and end_id
    def retreive_utterances_range(self, start_id, end_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM utterances
            WHERE id >= ? AND id <= ?
            ORDER BY created_at ASC
        ''', (start_id, end_id))
        entries = cursor.fetchall()
        # convert entries into a list of dictionaries
        entries_list = []
        for entry in entries:
            entries_list.append({
                'id': entry[0],
                'speaker': entry[1],
                'utterance': entry[2],
                'created_at': entry[3]
            })
        return entries_list

    # Return a range of utterances between start_id and end_id
    def retreive_utterances_since_id(self, utterance_id):
        cursor = self.conn.cursor()
        cursor.execute(f'''
            SELECT * FROM utterances
            WHERE id > {utterance_id}
            ORDER BY created_at ASC
        ''')
        entries = cursor.fetchall()
        # convert entries into a list of dictionaries
        entries_list = []
        for entry in entries:
            entries_list.append({
                'id': entry[0],
                'speaker': entry[1],
                'utterance': entry[2],
                'created_at': entry[3]
            })
        return entries_list
