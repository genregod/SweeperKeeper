import logging
import requests
from bs4 import BeautifulSoup
from database import get_accounts
from casino_locator import KNOWN_CASINOS

class CoinClaimer:
    def __init__(self, db):
        self.db = db
        self.casino_handlers = {
            "Chumba Casino": self.claim_chumba_casino,
            "LuckyLand Slots": self.claim_luckyland_slots,
            "Global Poker": self.claim_global_poker,
            "Funzpoints": self.claim_funzpoints,
            "Pulsz Casino": self.claim_pulsz_casino,
        }

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

    def claim_chumba_casino(self, account):
        return self._generic_claim(account, "https://www.chumbacasino.com/claim-coins", 
                                   login_selector="#login-form", 
                                   claim_selector="#claim-coins-button")

    def claim_luckyland_slots(self, account):
        return self._generic_claim(account, "https://www.luckylandslots.com/claim-coins", 
                                   login_selector="#login-form", 
                                   claim_selector="#claim-coins-button")

    def claim_global_poker(self, account):
        return self._generic_claim(account, "https://www.globalpoker.com/claim-coins", 
                                   login_selector="#login-form", 
                                   claim_selector="#claim-coins-button")

    def claim_funzpoints(self, account):
        return self._generic_claim(account, "https://www.funzpoints.com/claim-coins", 
                                   login_selector="#login-form", 
                                   claim_selector="#claim-coins-button")

    def claim_pulsz_casino(self, account):
        return self._generic_claim(account, "https://www.pulsz.com/claim-coins", 
                                   login_selector="#login-form", 
                                   claim_selector="#claim-coins-button")

    def _generic_claim(self, account, claim_url, login_selector, claim_selector):
        try:
            session = requests.Session()
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
        cursor = self.db.cursor()
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

def setup_coin_claimer(db):
    return CoinClaimer(db)
