import schedule
import time
import logging

def setup_scheduler(coin_claimer):
    logging.info("Setting up scheduler")
    
    def claim_all_coins():
        cursor = coin_claimer.db.cursor()
        cursor.execute("SELECT id FROM casinos")
        casino_ids = [row[0] for row in cursor.fetchall()]
        
        for casino_id in casino_ids:
            coin_claimer.claim_coins(casino_id)
    
    # Schedule coin claiming every 24 hours
    schedule.every(24).hours.do(claim_all_coins)
    
    # Run the scheduler in a separate thread
    import threading
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()
    
    return scheduler_thread

