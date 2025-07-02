import os
from dotenv import load_dotenv
import openai
import logging

# Load environment variables
load_dotenv()

# Load API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")  # For Instagram Graph API
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")  # Your Instagram Business Account ID

# Model constants
SUMMARIZE_MODEL = "gpt-4o"
CAPTION_MODEL = "gpt-4.1-nano"
IMAGE_MODEL = "gpt-4.1-nano"

# Social Media Planner agent config
AGENT = {
    "name": "Social Media Planner",
    "provider": "openai",
    "model": "gpt-4o"
}

# RSS feeds
RSS_FEEDS = [
    "http://www.agd.org/myagd/subscriptions/rss/kyt_hottopics.xml",
    "http://www.agd.org/myagd/subscriptions/rss/kyt_factoidweek.xml",
    "https://www.dentalhealth.org/handlers/rss.ashx?feed=1",
    "https://askthedentist.com/feed/"
]

# CORS origins
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Setup OpenAI client
def get_openai_client():
    """Get configured OpenAI client"""
    if not OPENAI_API_KEY:
        raise Exception("OPENAI_API_KEY not set")
    return openai.OpenAI(api_key=OPENAI_API_KEY)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__) 