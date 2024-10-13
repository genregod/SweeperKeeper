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
        accounts = get_accounts(self.coin_claimer.db)
        for account in accounts:
            account_id = account[0]
            schedule.every().day.at("00:00").do(self.coin_claimer.claim_coins, account_id)
        logging.info("Scheduled daily coin claiming for all accounts")

def setup_scheduler(coin_claimer):
    scheduler = Scheduler(coin_claimer)
    scheduler.schedule_coin_claiming()
    scheduler.start()
    return scheduler
