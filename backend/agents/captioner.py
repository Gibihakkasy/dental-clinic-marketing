import logging
from ..config import get_openai_client, CAPTION_MODEL

logger = logging.getLogger(__name__)

def generate_caption(summary: str) -> str:
    """
    Generate an Instagram caption based on an article summary.
    
    Args:
        summary: Article summary text
        
    Returns:
        Generated Instagram caption
    """
    try:
        client = get_openai_client()
        
        caption_prompt = (
            f"Given this summary of a dental news article, write a highly engaging Instagram caption for a dental clinic's Indonesian patients in Bahasa Indonesia. Don't use em-dashes. Always include call to action, popular hashtags, and moderate amount of emojis. never offer anything free.\n"
            f"Summary: {summary}\n"
        )
        
        caption_resp = client.chat.completions.create(
            model=CAPTION_MODEL,
            messages=[{"role": "user", "content": caption_prompt}]
        )
        
        caption = getattr(caption_resp.choices[0].message, 'content', None)
        if caption:
            caption = caption.strip()
        else:
            caption = "(No caption returned)"
            
        logger.info("Successfully generated Instagram caption")
        return caption
        
    except Exception as e:
        logger.error(f"Failed to generate Instagram caption: {str(e)}")
        return "(Caption generation failed)" 