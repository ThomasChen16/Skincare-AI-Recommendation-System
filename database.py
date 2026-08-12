# database.py is the bridge between the backend and the database
# Open SQLITE connection
# Return cursors
# Commit changes
# Hold the add / retrieve / update for each table? Maybe idk if needed for this product

import sqlite3

DB_PATH = "data/feedback.db"

def get_connection():
    # Establish a connection to the SQLite database
    conn = sqlite3.connect(DB_PATH)
    
    # This allow us to access the columns by name
    conn.row_factory = sqlite3.Row
    
    return conn

def init_db():
    # Establishes connection to SQLite database and access to columns by name
    conn = get_connection
    
    # Pen that writes SQL commands to the database
    cursor = conn.cursor()
    
    # Create table to hold user's profile data
    cursor.execute("""
        CREATE TABLE IF NOT EXIST feedback (
            id              INTEGER     AUTOINCREMENT,
            unique_id       TEXT        NOT NULL,
            product         TEXT        NOT NULL,
            product_type    TEXT,
            rating          TEXT        NOT NULL,
            routine_time    TEXT,
            created_at      TEXT        DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id)
        )
    """)
    
    # save changes and close connection
    conn.commit()
    
    conn.close()
    
    
    
    