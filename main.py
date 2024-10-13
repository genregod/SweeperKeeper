import logging
from database import initialize_database, store_casino_info
from user_interface import start_cli
from casino_locator import locate_casinos
from coin_claimer import setup_coin_claimer
from scheduler import setup_scheduler

# Configure logging
logging.basicConfig(filename='sweeper_keeper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("Starting SweeperKeeper")
    
    # Initialize database
    db = initialize_database()
    
    # Locate social casinos
    casinos = locate_casinos()
    
    # Store casino information in the database
    store_casino_info(db, casinos)
    
    # Setup coin claimer
    coin_claimer = setup_coin_claimer(db)
    
    # Setup scheduler for automated tasks
    scheduler = setup_scheduler(coin_claimer)
    
    # Start command-line interface
    start_cli(db, casinos, coin_claimer, scheduler)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"An error occurred in the main program: {str(e)}")
