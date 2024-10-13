import logging
from database import initialize_database, store_casino_info, add_test_accounts
from user_interface import start_cli
from casino_locator import locate_casinos
from coin_claimer import setup_coin_claimer
from scheduler import setup_scheduler

# Configure logging
logging.basicConfig(filename='sweeper_keeper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Add a console handler to see logs in the terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

def main():
    logging.info("Starting SweeperKeeper")
    
    # Initialize database
    db = initialize_database()
    
    # Add test accounts if the database is empty
    add_test_accounts(db)
    
    # Locate social casinos
    casinos = locate_casinos()
    
    # Store casino information in the database
    store_casino_info(db, casinos)
    
    # Setup coin claimer
    coin_claimer = setup_coin_claimer(db)
    
    # Test multi-threaded coin claiming
    logging.info("Starting multi-threaded coin claiming test")
    results = coin_claimer.claim_coins_for_all_accounts()
    logging.info(f"Multi-threaded coin claiming test results: {results}")
    
    success_count = sum(1 for _, success in results if success)
    failure_count = len(results) - success_count
    
    logging.info(f"Multi-threaded coin claiming summary:")
    logging.info(f"Total accounts processed: {len(results)}")
    logging.info(f"Successful claims: {success_count}")
    logging.info(f"Failed claims: {failure_count}")
    
    for account_id, success in results:
        if success:
            logging.info(f"Successfully claimed coins for account {account_id}")
        else:
            logging.warning(f"Failed to claim coins for account {account_id}")
    
    # Setup scheduler for automated tasks
    scheduler = setup_scheduler(coin_claimer)
    
    # Start command-line interface
    start_cli(db, casinos, coin_claimer, scheduler)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"An error occurred in the main program: {str(e)}")
