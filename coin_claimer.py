from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from utils import decrypt_password

class CoinClaimer:
    def __init__(self, db_connection):
        self.db = db_connection
        self.driver = None

    def setup_driver(self):
        if not self.driver:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            self.driver = webdriver.Chrome(options=chrome_options)

    def claim_coins(self, casino_id):
        self.setup_driver()
        
        # Get casino info and user credentials
        cursor = self.db.cursor()
        cursor.execute("SELECT website FROM casinos WHERE id = ?", (casino_id,))
        website = cursor.fetchone()[0]
        
        cursor.execute("SELECT username, password_hash FROM users WHERE casino_id = ?", (casino_id,))
        username, password_hash = cursor.fetchone()
        password = decrypt_password(password_hash)
        
        try:
            # Navigate to the casino website
            self.driver.get(website)
            
            # Login (customize based on the actual website structure)
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.send_keys(username)
            
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(password)
            
            login_button = self.driver.find_element(By.ID, "login-button")
            login_button.click()
            
            # Navigate to free coins page and claim (customize based on the actual website structure)
            free_coins_link = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.LINK_TEXT, "Free Coins"))
            )
            free_coins_link.click()
            
            claim_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "claim-button"))
            )
            claim_button.click()
            
            logging.info(f"Successfully claimed free coins for casino {casino_id}")
            return True
        
        except Exception as e:
            logging.error(f"Error claiming coins for casino {casino_id}: {str(e)}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

def setup_coin_claimer(db_connection):
    return CoinClaimer(db_connection)
