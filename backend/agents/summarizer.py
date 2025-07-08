import logging
from ..config import get_openai_client, SUMMARIZE_MODEL

logger = logging.getLogger(__name__)

def generate_summary(article_title: str, article_url: str) -> str:
    """
    Generate a summary for a dental news article using OpenAI Response API.
    
    Args:
        article_title: Title of the article
        article_url: URL of the article
        
    Returns:
        Generated summary text
    """
    try:
        client = get_openai_client()
        
        summary_prompt = (
            f"Summarize the following dental news article for dentists audience in Bahasa Indonesia.\n"
            f"Title: {article_title}\n"
            f"URL: {article_url}\n"
            f"Return a comprehensive summary. Without flavor text, e.g. here's the summary:, or repeating the title in the summary."
        )
        
        # Use OpenAI Response API with web_search tool for detailed summarization
        summary_resp = client.responses.create(
            model=SUMMARIZE_MODEL,
            input=summary_prompt,
            tools=[{"type": "web_search"}]  # type: ignore
        )
        
        summary = getattr(summary_resp, 'output_text', None)
        if summary:
            summary = summary.strip()
        else:
            summary = "(No summary returned)"
            
        logger.info(f"Successfully generated summary for article: {article_title}")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to generate summary for article {article_title}: {str(e)}")
        return "(Summary generation failed)"