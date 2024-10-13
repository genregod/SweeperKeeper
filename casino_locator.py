import requests
from bs4 import BeautifulSoup
import logging
from config import SEARCH_API_KEY, SEARCH_ENGINE_ID

def locate_casinos():
    logging.info("Locating social casinos")
    casinos = []
    
    # Use a search engine API to find social casino websites
    search_query = "social casino free sweeps coins"
    search_url = f"https://www.googleapis.com/customsearch/v1?key={SEARCH_API_KEY}&cx={SEARCH_ENGINE_ID}&q={search_query}"
    
    try:
        response = requests.get(search_url)
        search_results = response.json()
        
        for item in search_results.get('items', []):
            name = item['title']
            website = item['link']
            casinos.append({
                'name': name,
                'website': website
            })
    
    except Exception as e:
        logging.error(f"Error searching for social casinos: {str(e)}")
    
    logging.info(f"Found {len(casinos)} potential social casinos")
    return casinos

def verify_casino(website):
    """Verify if the website is actually a social casino"""
    try:
        response = requests.get(website, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for keywords that suggest it's a social casino
        keywords = ['free coins', 'sweeps coins', 'slots', 'casino games', 'play now']
        text_content = soup.get_text().lower()
        
        if any(keyword in text_content for keyword in keywords):
            return True
        
    except Exception as e:
        logging.error(f"Error verifying casino {website}: {str(e)}")
    
    return False
