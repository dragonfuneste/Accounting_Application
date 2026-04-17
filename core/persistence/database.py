import os
import sqlite3
import pandas as pd
import logging
from ..variables.variable import DATA_DIRECTORY

class Database:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.path_db = os.path.join(DATA_DIRECTORY, f"{db_name}.db")

        if not os.path.exists(DATA_DIRECTORY):
            os.makedirs(DATA_DIRECTORY)

        if not os.path.exists(self.path_db):
            self.create_empty_db()

    def create_empty_db(self):
        conn = sqlite3.connect(self.path_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS _metadata_accounts (
                account_name TEXT PRIMARY KEY,
                devise TEXT,
                state INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def list_tables(self):
        conn = sqlite3.connect(self.path_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        conn.close()
        return tables

    def read_table(self, name: str):
        conn = sqlite3.connect(self.path_db)
        df = pd.read_sql(f"SELECT * FROM {name}", conn)
        conn.close()
        return df

    def write_table(self, name: str, df: pd.DataFrame):
        conn = sqlite3.connect(self.path_db)
        df.to_sql(name, conn, if_exists='replace', index=False)
        conn.close()

    def drop_table(self, name: str):
        conn = sqlite3.connect(self.path_db)
        conn.execute(f'DROP TABLE IF EXISTS "{name}"')
        conn.commit()
        conn.close()
