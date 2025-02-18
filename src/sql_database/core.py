import json
import sqlite3
from datetime import datetime
from sql_database.ltm import SQLDatabaseLTM
from sql_database.stm import SQLDatabaseSTM
from sql_database.states import SQLDatabaseStates
from sql_database.auth import SQLDatabaseAuth
import os
import utils

class SQLDatabase:

    reset_db = False
    reset_conversations = True
    #reset_db = True

    def __init__(self, system_container, data_container):
        # Noramlize system_container and data_container to ensure theya re suitable for folder names
        system_container = utils.normalize_folder_name(system_container)
        data_container = utils.normalize_folder_name(data_container)

        db_file=f"db/{system_container}/{data_container}/sql.db"
        # Make the folders if they don't exist
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        self.conn = sqlite3.connect(db_file)
        if system_container != "shared":
            self.db_ltm = SQLDatabaseLTM(self.conn)
            self.db_stm = SQLDatabaseSTM(self.conn)
            self.db_states = SQLDatabaseStates(self.conn)
            self.db_ltm.create_tables()
            self.db_stm.create_tables()
            self.db_states.create_tables()
        else:
            self.db_auth = SQLDatabaseAuth(self.conn)
            self.db_auth.create_tables()
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        self.conn.commit()

