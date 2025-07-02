import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def extract_article_text(url: str, max_paragraphs: int = 5) -> str:
    """
    Extract text content from a web page URL.
    
    Args:
        url: The URL to extract text from
        max_paragraphs: Maximum number of paragraphs to extract
        
    Returns:
        Extracted text content as a string
    """
    try:
        resp = requests.get(url, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        paragraphs = soup.find_all("p")
        return " ".join(p.get_text().strip() for p in paragraphs[:max_paragraphs])
    except Exception as e:
        logger.error(f"Failed to extract text from {url}: {str(e)}")
        return "" 