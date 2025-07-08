import os
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

# Import our modules
from .db.cache import cache, get_topic_key

from .config import AGENT, CORS_ORIGINS, logger, INSTAGRAM_ACCESS_TOKEN
from .rss.fetcher import fetch_grouped_rss_news, fetch_unique_rss_news
from .agents.summarizer import generate_summary
from .agents.captioner import generate_caption
from .agents.image_prompter import generate_image_prompt, generate_image_from_prompt
from .utils.cloudinary import upload_to_cloudinary
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

class TopicRequest(BaseModel):
    topic: str = Field(..., description="The topic to generate content for")

class TopicResponse(BaseModel):
    id: str
    topic: str
    summary: str
    caption: str
    image_prompt: str
    sources: List[str]
    created_at: float

class TopicListItem(BaseModel):
    id: str
    topic: str
    preview: str
    created_at: float

class ImageGenerationRequest(BaseModel):
    prompt: str
    force_regenerate: bool = False
    article_link: Optional[str] = None

@app.post("/check_cached_image")
def check_cached_image(request: ImageGenerationRequest):
    """
    Check if an image exists in cache for the given prompt without generating a new one.
    Returns the cached image URL if found, or None if not found.
    """
    try:
        cache_key = f"image_gpt:{request.prompt.strip()}"
        cached_url = cache.get(cache_key)
        return {"image_url": cached_url, "from_cache": cached_url is not None}
    except Exception as e:
        logger.error(f"Error in check_cached_image: {str(e)}")
        return {"image_url": None, "from_cache": False, "error": str(e)}

@app.post("/generate_image_gpt")
def generate_image_gpt(request: ImageGenerationRequest):
    """
    Generate an image using GPT-image-1 (DALL-E), cache by prompt, upload to Cloudinary, and return the Cloudinary URL.
    If force_regenerate is True, always generate a new image and update the cache.
    """
    try:
        cache_key = f"image_gpt:{request.prompt.strip()}"
        from_cache = False
        # Check cache unless force_regenerate
        if not request.force_regenerate:
            cached_url = cache.get(cache_key)
            if cached_url:
                return {"image_url": cached_url, "from_cache": True}
        # Generate image
        image_path = generate_image_from_prompt(request.prompt)
        # Upload to Cloudinary
        public_id = f"dental_gptimg_{uuid.uuid4().hex}"
        image_url = upload_to_cloudinary(image_path, public_id=public_id)
        # Update cache
        cache.set(cache_key, image_url)
        return {"image_url": image_url, "from_cache": False}
    except Exception as e:
        logger.error(f"Error in generate_image_gpt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
        
        # Only save to cache if all generations are successful
        error_placeholders = ["(Processing failed)", "(Caption generation failed)", "(Image prompt generation failed)"]
        if (
            summary not in error_placeholders and
            caption not in error_placeholders and
            image_prompt not in error_placeholders and
            summary.strip() != "" and caption.strip() != "" and image_prompt.strip() != ""
        ):
            cache.save_article({
                'title': article['title'],
                'link': article['link'],
                'summary': summary,
                'caption': caption,
                'image_prompt': image_prompt
            })
            logger.info(f"Successfully processed and cached article: {article['title']}")
        else:
            logger.warning(f"Not caching article {article['title']} due to failed generation(s)")
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

@app.post("/regenerate_summary")
async def regenerate_summary(request: dict):
    """Regenerate summary for an article or topic."""
    try:
        if 'article_link' in request:
            # Article summary regeneration
            article_link = request['article_link']
            article = cache.get_article(article_link)
            if not article:
                raise HTTPException(status_code=404, detail="Article not found in cache")
            new_summary = generate_summary(article['title'], article['link'])
            # Only update cache if summary is successful
            if new_summary and new_summary.strip() != "" and new_summary != "(Processing failed)":
                article['summary'] = new_summary
                cache.save_article(article)
                cache_status = True
            else:
                cache_status = False
            return {"summary": new_summary, "cache_status": cache_status}
        elif 'topic_id' in request:
            # Topic summary regeneration
            topic_id = request['topic_id']
            topic = cache.get_topic(topic_id)
            if not topic:
                raise HTTPException(status_code=404, detail="Topic not found in cache")
            new_summary = generate_summary(topic['topic'], topic['topic'])
            # Only update cache if summary is successful
            if new_summary and new_summary.strip() != "" and new_summary != "(Processing failed)":
                topic['summary'] = new_summary
                cache.save_topic(topic)
                cache_status = True
            else:
                cache_status = False
            return {"summary": new_summary, "cache_status": cache_status}
        else:
            raise HTTPException(status_code=400, detail="Must provide article_link or topic_id")
    except Exception as e:
        logger.error(f"Error regenerating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error regenerating summary: {str(e)}")

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
        
        # Only update cache if caption is successful
        if new_caption and new_caption.strip() != "" and new_caption != "(Caption generation failed)":
            article['caption'] = new_caption
            cache.save_article(article)
            cache_status = True
        else:
            cache_status = False
        return {"caption": new_caption, "cache_status": cache_status}
        
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
async def get_rss_articles_grouped():
    """Get RSS articles grouped by feed."""
    return fetch_grouped_rss_news()

# Topic Management Endpoints

@app.post("/topics/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_from_topic(request: TopicRequest, background_tasks: BackgroundTasks):
    """
    Start generating content for a new topic.
    Returns a generation ID that can be used to check progress.
    """
    try:
        generation_id = str(uuid.uuid4())
        
        # Start background task
        background_tasks.add_task(
            _process_topic_generation,
            topic=request.topic,
            generation_id=generation_id
        )
        
        return {
            "status": "started", 
            "generation_id": generation_id,
            "message": "Topic generation started. Use the generation_id to check progress."
        }
    except Exception as e:
        logger.error(f"Error starting topic generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/topics", response_model=List[TopicListItem])
async def list_topics(limit: int = 100, offset: int = 0):
    """List all cached topics with pagination."""
    try:
        return cache.list_topics(limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Error listing topics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/topics/{topic_id}", response_model=TopicResponse)
async def get_topic(topic_id: str):
    """Get details of a specific topic by ID."""
    try:
        topic = cache.get_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        return topic
    except Exception as e:
        logger.error(f"Error getting topic {topic_id}: {str(e)}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Topic not found")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(topic_id: str):
    """Delete a topic by ID."""
    try:
        if not topic_id.startswith("topic_"):
            raise HTTPException(status_code=400, detail="Invalid topic ID format")
            
        if not cache.delete_topic(topic_id):
            raise HTTPException(status_code=404, detail="Topic not found")
            
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting topic {topic_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/topics/{generation_id}/status")
async def check_generation_status(generation_id: str):
    """Check the status of a topic generation task."""
    try:
        # Try to get the final result first
        result = cache.get(f"result_{generation_id}")
        if result:
            return result
            
        # If no result yet, check progress
        progress = cache.get(f"progress_{generation_id}")
        if progress:
            return progress
            
        raise HTTPException(status_code=404, detail="Generation ID not found")
    except Exception as e:
        logger.error(f"Error checking generation status {generation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task for processing topic generation
async def _process_topic_generation(topic: str, generation_id: str):
    """Background task to generate content for a topic."""
    try:
        # Update progress
        cache.set(f"progress_{generation_id}", {
            "status": "searching",
            "topic": topic,
            "timestamp": time.time()
        })
        
        # Step 1: Search and summarize the topic
        summary = await _search_and_summarize_topic(topic)
        
        # Step 2: Generate caption
        cache.set(f"progress_{generation_id}", {
            "status": "generating_caption",
            "topic": topic,
            "summary": summary,
            "timestamp": time.time()
        })
        caption = generate_caption(summary)
        
        # Step 3: Generate image prompt
        cache.set(f"progress_{generation_id}", {
            "status": "generating_image_prompt",
            "topic": topic,
            "summary": summary,
            "caption": caption,
            "timestamp": time.time()
        })
        image_prompt = generate_image_prompt(summary)
        
        # Save the final result
        topic_data = {
            "id": get_topic_key(topic),
            "topic": topic,
            "summary": summary,
            "caption": caption,
            "image_prompt": image_prompt,
            "sources": ["Web Search"],
            "created_at": time.time(),
            "status": "completed"
        }
        
        # Save to cache
        cache.save_topic(topic_data)
        cache.set(f"result_{generation_id}", topic_data)
        
        # Also update progress
        cache.set(f"progress_{generation_id}", topic_data)
        
        return topic_data
        
    except Exception as e:
        logger.error(f"Error in topic generation: {str(e)}")
        error_data = {
            "status": "error",
            "error": str(e),
            "topic": topic,
            "timestamp": time.time()
        }
        cache.set(f"progress_{generation_id}", error_data)
        cache.set(f"result_{generation_id}", error_data)
        raise

async def _search_and_summarize_topic(topic: str) -> str:
    """Search the web for information about a topic and generate a short and concise paragraph summary for a dentist audience. Include all source links."""
    try:
        # Use the existing summarizer with a special prompt for topic-based summarization
        # This leverages the existing OpenAI integration with web search
        return generate_summary(
            article_title=f"Search results for: {topic}",
            article_url=topic  # This will be used as context in the prompt
        )
    except Exception as e:
        logger.error(f"Error in topic search and summarization: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary for topic: {str(e)}"
        )