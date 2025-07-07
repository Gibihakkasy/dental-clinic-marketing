import os
import requests
import logging
from typing import Optional, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstagramAPIError(Exception):
    """Custom exception for Instagram API errors"""
    pass

class InstagramAPI:
    """
    A class to handle Instagram Graph API operations.
    """
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self, access_token: str, page_id: str, instagram_business_account_id: str):
        """
        Initialize the Instagram API client.
        
        Args:
            access_token (str): Facebook Page Access Token with required permissions
            page_id (str): Facebook Page ID
            instagram_business_account_id (str): Instagram Business Account ID
        """
        self.access_token = access_token
        self.page_id = page_id
        self.instagram_business_account_id = instagram_business_account_id
        self.base_url = f"{self.BASE_URL}/{self.instagram_business_account_id}"
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make an HTTP request to the Instagram Graph API.
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint
            data (Optional[Dict]): Request payload
            
        Returns:
            Dict: API response
        """
        url = f"{self.base_url}/{endpoint}"
        params = {
            'access_token': self.access_token
        }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, params=params, json=data)
            else:
                raise InstagramAPIError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Instagram API request failed: {str(e)}"
            logger.error(error_msg)
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise InstagramAPIError(error_msg)
    
    def post_to_instagram(self, caption: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a post on Instagram.
        
        Args:
            caption (str): The caption for the Instagram post
            image_url (str, optional): URL of the image to post. If not provided, 
                                     uses the default dental clinic image.
                                      
        Returns:
            Dict: API response containing the post ID and other metadata
        """
        # Use the provided image URL or fall back to the default dental clinic image
        media_url = image_url or "https://res.cloudinary.com/daqhgqqcz/image/upload/v1751690835/Download_Indonesian_dental_clinic_cym9gk.jpg"
        
        # Step 1: Create a container for the media
        container_data = {
            'image_url': media_url,
            'caption': caption,
            'access_token': self.access_token
        }
        
        try:
            # Create the media container
            container_response = requests.post(
                f"{self.BASE_URL}/{self.instagram_business_account_id}/media",
                data=container_data
            )
            container_response.raise_for_status()
            container_id = container_response.json().get('id')
            
            if not container_id:
                raise InstagramAPIError("Failed to create media container: No container ID returned")
            
            # Step 2: Publish the container
            publish_data = {
                'creation_id': container_id,
                'access_token': self.access_token
            }
            
            publish_response = requests.post(
                f"{self.BASE_URL}/{self.instagram_business_account_id}/media_publish",
                data=publish_data
            )
            publish_response.raise_for_status()
            
            return {
                'success': True,
                'post_id': publish_response.json().get('id'),
                'container_id': container_id,
                'message': 'Post created successfully'
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to post to Instagram: {str(e)}"
            logger.error(error_msg)
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise InstagramAPIError(error_msg)

def get_instagram_client() -> InstagramAPI:
    """
    Helper function to create and return an InstagramAPI client instance.
    
    Environment variables required:
    - FACEBOOK_ACCESS_TOKEN: Your Facebook Page Access Token
    - FACEBOOK_PAGE_ID: Your Facebook Page ID
    - INSTAGRAM_BUSINESS_ACCOUNT_ID: Your Instagram Business Account ID
    
    Returns:
        InstagramAPI: An instance of the InstagramAPI client
    """
    access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
    page_id = os.getenv('FACEBOOK_PAGE_ID')
    instagram_business_account_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
    
    if not all([access_token, page_id, instagram_business_account_id]):
        missing = []
        if not access_token:
            missing.append('FACEBOOK_ACCESS_TOKEN')
        if not page_id:
            missing.append('FACEBOOK_PAGE_ID')
        if not instagram_business_account_id:
            missing.append('INSTAGRAM_BUSINESS_ACCOUNT_ID')
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return InstagramAPI(access_token, page_id, instagram_business_account_id)
