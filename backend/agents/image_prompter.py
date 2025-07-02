import logging
from ..config import get_openai_client, IMAGE_MODEL

logger = logging.getLogger(__name__)

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
            model=IMAGE_MODEL,
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