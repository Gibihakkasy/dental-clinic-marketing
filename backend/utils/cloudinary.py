import os
import cloudinary
import cloudinary.uploader
from typing import Optional

# Configure Cloudinary with environment variables
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

def upload_to_cloudinary(image_path: str, public_id: Optional[str] = None) -> str:
    """
    Uploads an image to Cloudinary and returns the secure URL.
    Args:
        image_path (str): Path to the local image file.
        public_id (Optional[str]): Optional Cloudinary public ID for the image.
    Returns:
        str: The secure URL of the uploaded image.
    """
    response = cloudinary.uploader.upload(image_path, public_id=public_id, overwrite=True, resource_type="image")
    return response['secure_url']
