import schedule
import time
import threading
import logging
from database import get_accounts

class Scheduler:
    def __init__(self, coin_claimer):
        self.coin_claimer = coin_claimer
        self.running = False

    def start(self):
        self.running = True
        thread = threading.Thread(target=self.run_scheduler)
        thread.start()

    def stop(self):
        self.running = False

    def run_scheduler(self):
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def schedule_coin_claiming(self):
        schedule.every().day.at("00:00").do(self.claim_coins_for_all_accounts)
        logging.info("Scheduled daily coin claiming for all accounts")

    def claim_coins_for_all_accounts(self):
        results = self.coin_claimer.claim_coins_for_all_accounts()
        for account_id, success in results:
            if success:
                logging.info(f"Successfully claimed coins for account {account_id}")
            else:
                logging.warning(f"Failed to claim coins for account {account_id}")

def setup_scheduler(coin_claimer):
    scheduler = Scheduler(coin_claimer)
    scheduler.schedule_coin_claiming()
    scheduler.start()
    return scheduler
