import sqlite3
import logging

def initialize_database():
    logging.info("Initializing database")
    conn = sqlite3.connect('sweeper_keeper.db')
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
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY,
            casino_id INTEGER,
            username TEXT NOT NULL,
            next_reminder DATETIME,
            auto_claim BOOLEAN DEFAULT 0,
            FOREIGN KEY (casino_id) REFERENCES casinos (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coin_claims (
            id INTEGER PRIMARY KEY,
            account_id INTEGER,
            claim_time DATETIME,
            amount REAL,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
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

def store_account_info(conn, casino_id, username, auto_claim=False):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO accounts (casino_id, username, auto_claim)
        VALUES (?, ?, ?)
    ''', (casino_id, username, auto_claim))
    conn.commit()
    logging.info(f"Stored account information for user {username}")

def get_accounts(conn):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT accounts.id, casinos.name, accounts.username, accounts.next_reminder, accounts.auto_claim
        FROM accounts
        JOIN casinos ON accounts.casino_id = casinos.id
    ''')
    return cursor.fetchall()

def log_coin_claim(conn, account_id, amount):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO coin_claims (account_id, claim_time, amount)
        VALUES (?, CURRENT_TIMESTAMP, ?)
    ''', (account_id, amount))
    conn.commit()
    logging.info(f"Logged coin claim for account {account_id}: {amount} coins")

def get_coin_claim_history(conn, account_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT claim_time, amount
        FROM coin_claims
        WHERE account_id = ?
        ORDER BY claim_time DESC
    ''', (account_id,))
    return cursor.fetchall()

def add_test_accounts(conn):
    cursor = conn.cursor()
    
    # First, check if there are any accounts
    cursor.execute('SELECT COUNT(*) FROM accounts')
    account_count = cursor.fetchone()[0]
    
    if account_count == 0:
        # Add test casinos if they don't exist
        casinos = [
            ("Chumba Casino", "https://www.chumbacasino.com"),
            ("LuckyLand Slots", "https://www.luckylandslots.com"),
            ("Global Poker", "https://www.globalpoker.com"),
            ("Funzpoints", "https://www.funzpoints.com"),
            ("Pulsz Casino", "https://www.pulsz.com")
        ]
        
        for casino in casinos:
            cursor.execute('INSERT OR IGNORE INTO casinos (name, website) VALUES (?, ?)', casino)
        
        # Add test accounts
        test_accounts = [
            (1, "testuser1"),
            (2, "testuser2"),
            (3, "testuser3"),
            (4, "testuser4"),
            (5, "testuser5")
        ]
        
        for account in test_accounts:
            cursor.execute('INSERT INTO accounts (casino_id, username) VALUES (?, ?)', account)
        
        conn.commit()
        logging.info("Added test accounts to the database")
    else:
        logging.info(f"Database already contains {account_count} accounts. Skipping test account creation.")
