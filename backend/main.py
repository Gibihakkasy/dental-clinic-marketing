import os
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Tuple
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Import our modules
from .db.cache import cache

# Import our modules
from .config import AGENT, CORS_ORIGINS, logger
from .rss.fetcher import fetch_grouped_rss_news, fetch_unique_rss_news
from .agents.summarizer import generate_summary
from .agents.captioner import generate_caption
from .agents.image_prompter import generate_image_prompt
from .utils.doc_writer import generate_word_document
from .config import INSTAGRAM_ACCESS_TOKEN  # Add this to your config.py

# FastAPI app setup
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SummarizeRequest(BaseModel):
    user_message: Optional[str] = None

class InstagramPostRequest(BaseModel):
    caption: str
    article: Dict[str, str]

def _process_article_content(article: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, bool]]:
    """
    Process a single article to generate summary, caption, and image prompt.
    
    Args:
        article: Article data with title and link
        
    Returns:
        Tuple of (article_data, cache_status) where:
        - article_data: Article data with generated content
        - cache_status: Dictionary with cache status for each component
    """
    try:
        # Check cache first
        cached_article = cache.get_article(article['link'])
        
        if cached_article:
            logger.info(f"Retrieved article from cache: {article['title']}")
            article['summary'] = cached_article['summary']
            article['caption'] = cached_article['caption']
            article['imagePrompt'] = cached_article['image_prompt']
            return article, {
                'summary': True,
                'caption': True,
                'imagePrompt': True
            }
            
        # If not in cache, generate new content
        logger.info(f"Generating content for article: {article['title']}")
        
        # Generate summary
        summary = generate_summary(article['title'], article['link'])
        
        # Generate caption based on summary
        caption = generate_caption(summary)
        
        # Generate image prompt based on summary
        image_prompt = generate_image_prompt(summary)
        
        # Update article with generated content
        article['summary'] = summary
        article['caption'] = caption
        article['imagePrompt'] = image_prompt
        
        # Save to cache
        cache.save_article({
            'title': article['title'],
            'link': article['link'],
            'summary': summary,
            'caption': caption,
            'image_prompt': image_prompt
        })
        
        logger.info(f"Successfully processed and cached article: {article['title']}")
        return article, {
            'summary': False,
            'caption': False,
            'imagePrompt': False
        }
        
    except Exception as e:
        logger.error(f"Failed to process article {article.get('title', 'Unknown')}: {str(e)}")
        # Return article with error placeholders
        article['summary'] = "(Processing failed)"
        article['caption'] = "(Processing failed)"
        article['imagePrompt'] = "(Processing failed)"
        return article, {
            'summary': False,
            'caption': False,
            'imagePrompt': False
        }

@app.get("/bots")
def get_bots():
    """Get available bots/agents."""
    return [{"name": AGENT["name"], "role": "Creates Instagram content plan from latest dental news."}]

@app.post("/regenerate_caption")
async def regenerate_caption(request: dict):
    """Regenerate caption for an article."""
    try:
        article_link = request.get('article_link')
        if not article_link:
            raise HTTPException(status_code=400, detail="Article link is required")
        
        # Get the article from cache
        article = cache.get_article(article_link)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found in cache")
        
        # Generate new caption
        new_caption = generate_caption(article['summary'])
        
        # Update cache
        article['caption'] = new_caption
        cache.save_article(article)
        
        return {"caption": new_caption}
        
    except Exception as e:
        logger.error(f"Error regenerating caption: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error regenerating caption: {str(e)}")

@app.post("/regenerate_image_prompt")
async def regenerate_image_prompt(request: dict):
    """Regenerate image prompt for an article."""
    try:
        article_link = request.get('article_link')
        if not article_link:
            raise HTTPException(status_code=400, detail="Article link is required")
        
        # Get the article from cache
        article = cache.get_article(article_link)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found in cache")
        
        # Generate new image prompt
        new_image_prompt = generate_image_prompt(article['summary'])
        
        # Update cache
        article['image_prompt'] = new_image_prompt
        cache.save_article(article)
        
        return {"image_prompt": new_image_prompt}
        
    except Exception as e:
        logger.error(f"Error regenerating image prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error regenerating image prompt: {str(e)}")

@app.post("/generate_social_plan")
async def generate_social_plan(request: dict):
    """Generate social media content plan for selected articles."""
    try:
        # Get selected articles from request
        selected = request.get('selected', [])
        if not selected:
            raise HTTPException(status_code=400, detail="No articles selected")
        
        # Fetch RSS feeds
        grouped = fetch_grouped_rss_news()
        
        # Build lookup for selected articles
        selected_lookup = {(s['feed_url'], s['article_link']) for s in selected}
        
        # Process selected articles in parallel
        articles_to_process = []
        
        # First pass: identify which articles need processing
        for feed in grouped:
            for article in feed['articles']:
                is_selected = (feed['feed_url'], article['link']) in selected_lookup
                if is_selected:
                    # Check cache first
                    cached_article = cache.get_article(article['link'])
                    if cached_article and cached_article.get('title') == article.get('title'):
                        # Use cached content only if titles match
                        article['summary'] = cached_article['summary']
                        article['caption'] = cached_article['caption']
                        article['imagePrompt'] = cached_article['image_prompt']
                        article['cache_status'] = {
                            'caption': True,
                            'imagePrompt': True,
                            'summary': True
                        }
                    else:
                        # Add to processing queue
                        articles_to_process.append((feed, article))
                        article['cache_status'] = {
                            'caption': False,
                            'imagePrompt': False,
                            'summary': False
                        }   
                else:
                    # Set None for non-selected articles
                    article['summary'] = None
                    article['caption'] = None
                    article['imagePrompt'] = None
        
        # Process uncached articles in parallel
        # Process articles in parallel
        with ThreadPoolExecutor() as executor:
            futures = []
            for feed, article in articles_to_process:
                future = executor.submit(_process_article_content, article)
                futures.append((feed, article, future))
            
            # Wait for all futures to complete
            for feed, article, future in futures:
                try:
                    processed_article, cache_status = future.result()
                    article.update(processed_article)
                    # Preserve the cache status we set earlier
                    if 'cache_status' not in article:
                        article['cache_status'] = cache_status
                except Exception as e:
                    logger.error(f"Error processing article {article.get('title')}: {str(e)}")
                    article['error'] = str(e)
                    # Set cache status to false on error
                    article['cache_status'] = {
                        'caption': False,
                        'imagePrompt': False,
                        'summary': False
                    } 

        # Generate Word document
        filename = generate_word_document(grouped)
        
        return {"file": filename, "grouped": grouped}
        
    except Exception as e:
        logger.error(f"Error generating social plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/download/{filename}")
def download_file(filename: str):
    """Download generated Word document."""
    file_path = os.path.join("documents", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        file_path, 
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
        filename=filename
    )

@app.get("/get_rss_articles")
def get_rss_articles():
    """Get unique RSS articles."""
    return fetch_unique_rss_news()

@app.post("/post_to_instagram")
async def post_to_instagram(request: InstagramPostRequest):
    """Post content to Instagram."""
    try:
        # In a real implementation, you would use the Instagram Graph API here
        # This is a mock implementation
        caption = request.caption
        article = request.article
        
        # Log the post (in production, this would post to Instagram)
        logger.info(f"Posting to Instagram: {caption[:50]}...")
        logger.info(f"Article: {article.get('title')} - {article.get('link')}")
        
        # Simulate API call delay
        time.sleep(1)
        
        return {"status": "success", "message": "Posted to Instagram successfully"}
    except Exception as e:
        logger.error(f"Error posting to Instagram: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_rss_articles_grouped")
def get_rss_articles_grouped():
    """Get RSS articles grouped by feed."""
    return fetch_grouped_rss_news() 