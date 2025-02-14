import json


class SQLDatabaseStates:
    def __init__(self, conn):
        self.conn = conn

    def create_tables(self):
        # Long Term Memory State
        cursor = self.conn.cursor()
        # Create Persona State Table
        if 1 == 0:
            # Drop the table
            cursor.execute('''
                DROP TABLE IF EXISTS persona_states
            ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS persona_states (
                name TEXT PRIMARY KEY NOT NULL,
                state TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    # -------------------------------------------------------------------------------
    # Persona State
    # Store the current state of the persona, overwriting the previous state
    def set_persona_current_state(self, state):
        # Update the previous state row using an insert or replace
        cursor = self.conn.cursor()
        cursor.execute(f"""
INSERT INTO persona_states (name, state)
VALUES ('current_state', '{state}')
ON CONFLICT(name) DO UPDATE SET state = excluded.state;
""")
        self.conn.commit()

    def get_persona_current_state(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT state FROM persona_states
            WHERE name = "current_state"
        ''')
        # Return the state from the row or None if it doesn't exist
        row = cursor.fetchone()
        if row:
            return row[0]
        return None

    def set_persona_state_data(self, state_name, state_data):
        state_data_text = json.dumps(state_data)
        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO persona_states (name, state)
            VALUES (?, ?)
            ON CONFLICT(name) DO UPDATE SET state = excluded.state;""",
            (state_name, state_data_text))
        self.conn.commit()

    def get_persona_state_data(self, state_name):
        cursor = self.conn.cursor()
        cursor.execute(f'''
            SELECT state FROM persona_states
            WHERE name = "{state_name}"
        ''')
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None