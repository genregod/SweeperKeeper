import sqlite3
import logging
from utils import hash_password

def initialize_database():
    logging.info("Initializing database")
    conn = sqlite3.connect('casino_bot.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS casinos (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            website TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            casino_id INTEGER,
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            FOREIGN KEY (casino_id) REFERENCES casinos (id)
        )
    ''')
    
    conn.commit()
    return conn

def store_casino_info(conn, casinos):
    cursor = conn.cursor()
    for casino in casinos:
        cursor.execute('''
            INSERT OR REPLACE INTO casinos (name, website)
            VALUES (?, ?)
        ''', (casino['name'], casino['website']))
    conn.commit()
    logging.info(f"Stored information for {len(casinos)} casinos")

def store_user_credentials(conn, casino_id, username, password):
    cursor = conn.cursor()
    password_hash = hash_password(password)
    cursor.execute('''
        INSERT INTO users (casino_id, username, password_hash)
        VALUES (?, ?, ?)
    ''', (casino_id, username, password_hash))
    conn.commit()
    logging.info(f"Stored credentials for user {username}")

def get_user_credentials(conn, casino_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username, password_hash FROM users
        WHERE casino_id = ?
    ''', (casino_id,))
    return cursor.fetchone()

