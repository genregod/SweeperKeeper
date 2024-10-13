import sqlite3
from datetime import datetime, timedelta

class Analytics:
    def __init__(self, db_path='sweeper_keeper.db'):
        self.db_path = db_path

    def _get_db_connection(self):
        return sqlite3.connect(self.db_path)

    def get_total_coins_claimed(self, user_id, time_range=None):
        conn = self._get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT SUM(cc.amount)
        FROM coin_claims cc
        JOIN accounts a ON cc.account_id = a.id
        WHERE a.user_id = ?
        """
        params = [user_id]

        if time_range:
            query += " AND cc.claim_time >= ?"
            params.append((datetime.now() - time_range).strftime('%Y-%m-%d %H:%M:%S'))

        cursor.execute(query, params)
        result = cursor.fetchone()[0]
        conn.close()
        return result or 0

    def get_claim_success_rate(self, user_id, time_range=None):
        conn = self._get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT 
            COUNT(CASE WHEN cc.amount > 0 THEN 1 END) as successful_claims,
            COUNT(*) as total_attempts
        FROM coin_claims cc
        JOIN accounts a ON cc.account_id = a.id
        WHERE a.user_id = ?
        """
        params = [user_id]

        if time_range:
            query += " AND cc.claim_time >= ?"
            params.append((datetime.now() - time_range).strftime('%Y-%m-%d %H:%M:%S'))

        cursor.execute(query, params)
        successful_claims, total_attempts = cursor.fetchone()
        conn.close()

        if total_attempts > 0:
            return (successful_claims / total_attempts) * 100
        return 0

    def get_coins_claimed_by_casino(self, user_id, time_range=None):
        conn = self._get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT c.name, SUM(cc.amount)
        FROM coin_claims cc
        JOIN accounts a ON cc.account_id = a.id
        JOIN casinos c ON a.casino_id = c.id
        WHERE a.user_id = ?
        """
        params = [user_id]

        if time_range:
            query += " AND cc.claim_time >= ?"
            params.append((datetime.now() - time_range).strftime('%Y-%m-%d %H:%M:%S'))

        query += " GROUP BY c.name"

        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results

    def get_claim_history(self, user_id, limit=10):
        conn = self._get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT c.name, a.username, cc.claim_time, cc.amount
        FROM coin_claims cc
        JOIN accounts a ON cc.account_id = a.id
        JOIN casinos c ON a.casino_id = c.id
        WHERE a.user_id = ?
        ORDER BY cc.claim_time DESC
        LIMIT ?
        """

        cursor.execute(query, (user_id, limit))
        results = cursor.fetchall()
        conn.close()
        return results
