import logging
import requests
from bs4 import BeautifulSoup
from database import get_accounts
from casino_locator import KNOWN_CASINOS
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import sqlite3

class CoinClaimer:
    def __init__(self):
        self.thread_local = threading.local()
        self.casino_handlers = {
            "Chumba Casino": self.claim_chumba_casino,
            "LuckyLand Slots": self.claim_luckyland_slots,
            "Global Poker": self.claim_global_poker,
            "Funzpoints": self.claim_funzpoints,
            "Pulsz Casino": self.claim_pulsz_casino,
        }

    def get_db(self):
        if not hasattr(self.thread_local, 'db'):
            self.thread_local.db = sqlite3.connect('sweeper_keeper.db')
        return self.thread_local.db

    def claim_coins(self, account_id):
        logging.info(f"Attempting to claim coins for account {account_id}")
        account = self.get_account(account_id)
        if not account:
            logging.error(f"Account {account_id} not found")
            return False

        casino_name = account['casino_name']
        if casino_name in self.casino_handlers:
            return self.casino_handlers[casino_name](account)
        else:
            logging.error(f"No handler found for casino: {casino_name}")
            return False

    def claim_coins_for_all_accounts(self, max_workers=5):
        logging.info("Starting claim_coins_for_all_accounts method")
        accounts = self.get_accounts()
        logging.info(f"Found {len(accounts)} accounts to process")
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_account = {executor.submit(self.claim_coins, account[0]): account for account in accounts}
            for future in as_completed(future_to_account):
                account = future_to_account[future]
                try:
                    result = future.result()
                    logging.info(f"Coin claiming for account {account[0]} completed with result: {result}")
                    results.append((account[0], result))
                except Exception as exc:
                    logging.error(f"Account {account[0]} generated an exception: {exc}")
                    results.append((account[0], False))

        logging.info(f"claim_coins_for_all_accounts completed. Results: {results}")
        return results

    def get_session(self):
        if not hasattr(self.thread_local, "session"):
            self.thread_local.session = requests.Session()
        return self.thread_local.session

    def claim_chumba_casino(self, account):
        logging.info(f"Claiming coins for Chumba Casino account: {account['id']}")
        return self._generic_claim(account, "https://www.chumbacasino.com/claim-coins", 
                                   login_selector="#login-form", 
                                   claim_selector="#claim-coins-button")

    def claim_luckyland_slots(self, account):
        logging.info(f"Claiming coins for LuckyLand Slots account: {account['id']}")
        return self._generic_claim(account, "https://www.luckylandslots.com/claim-coins", 
                                   login_selector="#login-form", 
                                   claim_selector="#claim-coins-button")

    def claim_global_poker(self, account):
        logging.info(f"Claiming coins for Global Poker account: {account['id']}")
        return self._generic_claim(account, "https://www.globalpoker.com/claim-coins", 
                                   login_selector="#login-form", 
                                   claim_selector="#claim-coins-button")

    def claim_funzpoints(self, account):
        logging.info(f"Claiming coins for Funzpoints account: {account['id']}")
        return self._generic_claim(account, "https://www.funzpoints.com/claim-coins", 
                                   login_selector="#login-form", 
                                   claim_selector="#claim-coins-button")

    def claim_pulsz_casino(self, account):
        logging.info(f"Claiming coins for Pulsz Casino account: {account['id']}")
        return self._generic_claim(account, "https://www.pulsz.com/claim-coins", 
                                   login_selector="#login-form", 
                                   claim_selector="#claim-coins-button")

    def _generic_claim(self, account, claim_url, login_selector, claim_selector):
        try:
            session = self.get_session()
            login_url = f"{account['website']}/login"

            # Simulate login
            login_data = {"username": account['username'], "password": "placeholder_password"}
            login_response = session.post(login_url, data=login_data)
            
            if login_response.status_code != 200:
                logging.error(f"Failed to login for account {account['id']} on {account['casino_name']}")
                return False

            # Simulate claiming coins
            claim_response = session.get(claim_url)
            soup = BeautifulSoup(claim_response.text, 'html.parser')
            
            claim_button = soup.select_one(claim_selector)
            if claim_button:
                claim_result = session.post(claim_url, data={"claim": "true"})
                if "Coins claimed successfully" in claim_result.text:
                    logging.info(f"Successfully claimed coins for account {account['id']} on {account['casino_name']}")
                    return True
                else:
                    logging.warning(f"Failed to claim coins for account {account['id']} on {account['casino_name']}")
                    return False
            else:
                logging.warning(f"Claim button not found for account {account['id']} on {account['casino_name']}")
                return False

        except requests.RequestException as e:
            logging.error(f"Network error while claiming coins for account {account['id']} on {account['casino_name']}: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error claiming coins for account {account['id']} on {account['casino_name']}: {str(e)}")
            return False

    def get_account(self, account_id):
        db = self.get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT accounts.id, casinos.name, casinos.website, accounts.username
            FROM accounts
            JOIN casinos ON accounts.casino_id = casinos.id
            WHERE accounts.id = ?
        """, (account_id,))
        result = cursor.fetchone()
        if result:
            return {
                "id": result[0],
                "casino_name": result[1],
                "website": result[2],
                "username": result[3]
            }
        return None

    def get_accounts(self):
        db = self.get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT accounts.id, casinos.name, accounts.username, accounts.next_reminder, accounts.auto_claim
            FROM accounts
            JOIN casinos ON accounts.casino_id = casinos.id
        """)
        return cursor.fetchall()

def setup_coin_claimer():
    return CoinClaimer()
