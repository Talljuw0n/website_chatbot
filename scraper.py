# scraper.py
import requests
from bs4 import BeautifulSoup

def scrape_website(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove scripts and styles
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()

        # Get visible text
        text = ' '.join(soup.stripped_strings)
        return text
    except Exception as e:
        return f"Error scraping site: {e}"
