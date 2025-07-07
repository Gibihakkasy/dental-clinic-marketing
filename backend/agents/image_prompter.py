import logging
from ..config import get_openai_client, IMAGE_GENERATION_MODEL, IMAGE_PROMPT_MODEL

logger = logging.getLogger(__name__)

import os
import uuid
from typing import Optional
import requests

# Generate image using GPT-image-1 (DALL-E) and save locally
def generate_image_from_prompt(prompt: str, output_dir: Optional[str] = None) -> str:
    """
    Generate an image using GPT-image-1 (DALL-E) and save it locally.
    Args:
        prompt (str): The image prompt for generation.
        output_dir (Optional[str]): Directory to save the image. Defaults to './generated_images'.
    Returns:
        str: Path to the saved image file.
    """
    try:
        client = get_openai_client()
        output_dir = output_dir or os.path.join(os.getcwd(), 'generated_images')
        os.makedirs(output_dir, exist_ok=True)
        # Call the image generation API (use create for the latest OpenAI client)
        image_resp = client.images.generate(
            model=IMAGE_GENERATION_MODEL,
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        logger.debug(f"Image API response: {image_resp}")
        # Extract base64, handle unexpected response shapes
        import base64
        try:
            b64_image = image_resp.data[0].b64_json
        except (AttributeError, IndexError) as e:
            logger.error(f"Unexpected image response format: {image_resp}")
            raise ValueError("No image data returned from image generation API.")
        if not b64_image:
            logger.error("No image data returned from image generation API.")
            raise ValueError("No image data returned from image generation API.")
        filename = f"image_{uuid.uuid4().hex}.png"
        image_path = os.path.join(output_dir, filename)
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(b64_image))
        logger.info(f"Generated image and saved to {image_path}")
        return image_path
    except Exception as e:
        logger.error(f"Failed to generate image: {str(e)}")
        raise

def generate_image_prompt(summary: str) -> str:
    """
    Generate an image prompt for AI image generation based on an article summary.
    
    Args:
        summary: Article summary text
        
    Returns:
        Generated image prompt
    """
    try:
        client = get_openai_client()
        
        image_prompt_prompt = (
            f"Given this summary, write a prompt for an image generation AI to create an image for a dental clinic instagram post. The audience is potential patient of an Indonesian dental clinic. Prioritize photorealistic image of Indonesian. 2D cartoon can be added as flare or decoration. Return only the prompt, no other text.\n"
            f"Summary: {summary}\n"
        )
        
        image_prompt_resp = client.chat.completions.create(
            model=IMAGE_PROMPT_MODEL,
            messages=[{"role": "user", "content": image_prompt_prompt}]
        )
        
        image_prompt = getattr(image_prompt_resp.choices[0].message, 'content', None)
        if image_prompt:
            image_prompt = image_prompt.strip()
        else:
            image_prompt = "(No image prompt returned)"
            
        logger.info("Successfully generated image prompt")
        return image_prompt
        
    except Exception as e:
        logger.error(f"Failed to generate image prompt: {str(e)}")
        return "(Image prompt generation failed)"