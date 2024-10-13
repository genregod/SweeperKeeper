import logging
from casino_locator import locate_casinos, verify_casino
from database import initialize_database, store_casino_info
from coin_claimer import setup_coin_claimer
from scheduler import setup_scheduler
from user_interface import start_cli

# Configure logging
logging.basicConfig(filename='casino_bot.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("Starting Social Casino Bot")
    
    # Initialize database
    db = initialize_database()
    
    # Locate and store casino information
    potential_casinos = locate_casinos()
    verified_casinos = []
    for casino in potential_casinos:
        if verify_casino(casino['website']):
            verified_casinos.append(casino)
    
    store_casino_info(db, verified_casinos)
    
    # Setup coin claimer
    claimer = setup_coin_claimer(db)
    
    # Setup scheduler
    scheduler = setup_scheduler(claimer)
    
    # Start command-line interface
    start_cli(db, claimer, scheduler)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"An error occurred in the main program: {str(e)}")
