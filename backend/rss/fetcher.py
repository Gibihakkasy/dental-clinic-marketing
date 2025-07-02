import feedparser
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import logging
from .cleaner import clean_knowyourteeth_link
from ..config import RSS_FEEDS

logger = logging.getLogger(__name__)

def _parse_feed_entry(entry, seen_titles: set, seen_links: set) -> Dict[str, Any] | None:
    """
    Parse a single RSS feed entry.
    
    Args:
        entry: RSS feed entry
        seen_titles: Set of already seen titles
        seen_links: Set of already seen links
        
    Returns:
        Parsed article data or None if duplicate/invalid
    """
    title = entry.get("title")
    raw_link = entry.get("link")
    
    if isinstance(raw_link, list):
        raw_link = raw_link[0] if raw_link else None
    
    if not isinstance(raw_link, str):
        return None
        
    link = clean_knowyourteeth_link(raw_link)
    
    if not title or not link:
        return None
        
    if title in seen_titles or link in seen_links:
        return None
        
    seen_titles.add(title)
    seen_links.add(link)
    
    published = None
    if hasattr(entry, 'published_parsed') and entry.published_parsed and isinstance(entry.published_parsed, tuple):
        try:
            published = datetime.datetime(*entry.published_parsed[:6])
        except Exception:
            published = datetime.datetime.now()
    else:
        published = datetime.datetime.now()
        
    return {
        "title": title,
        "link": link,
        "published": published
    }

def _fetch_single_feed(url: str) -> Dict[str, Any]:
    """
    Fetch and parse a single RSS feed.
    
    Args:
        url: RSS feed URL
        
    Returns:
        Feed data with articles
    """
    try:
        feed = feedparser.parse(url)
        feed_title = url
        
        if hasattr(feed, 'feed') and isinstance(feed.feed, dict):
            feed_title = feed.feed.get("title", url)
            
        articles = []
        seen_titles = set()
        seen_links = set()
        
        for entry in feed.entries:
            if len(articles) >= 5:
                break
                
            article = _parse_feed_entry(entry, seen_titles, seen_links)
            if article:
                articles.append(article)
                
        return {
            "feed_title": feed_title,
            "feed_url": url,
            "articles": articles
        }
    except Exception as e:
        logger.error(f"Failed to fetch feed {url}: {str(e)}")
        return {
            "feed_title": url,
            "feed_url": url,
            "articles": []
        }

def fetch_grouped_rss_news() -> List[Dict[str, Any]]:
    """
    Fetch RSS feeds in parallel and return grouped articles.
    
    Returns:
        List of feed groups with articles
    """
    grouped = []
    
    # Use ThreadPoolExecutor for parallel fetching
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all feed fetching tasks
        future_to_url = {executor.submit(_fetch_single_feed, url): url for url in RSS_FEEDS}
        
        # Collect results as they complete
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                feed_data = future.result()
                grouped.append(feed_data)
            except Exception as e:
                logger.error(f"Exception occurred while fetching {url}: {str(e)}")
                # Add empty feed data for failed feeds
                grouped.append({
                    "feed_title": url,
                    "feed_url": url,
                    "articles": []
                })
    
    return grouped

def fetch_unique_rss_news() -> List[Dict[str, str]]:
    """
    Fetch RSS feeds and return unique articles sorted by date.
    
    Returns:
        List of unique articles with title and link
    """
    entries = []
    seen_titles = set()
    seen_links = set()
    
    # Use ThreadPoolExecutor for parallel fetching
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all feed fetching tasks
        future_to_url = {executor.submit(_fetch_single_feed, url): url for url in RSS_FEEDS}
        
        # Collect results as they complete
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                feed_data = future.result()
                for article in feed_data['articles']:
                    if article['title'] not in seen_titles and article['link'] not in seen_links:
                        seen_titles.add(article['title'])
                        seen_links.add(article['link'])
                        entries.append({
                            "title": article['title'],
                            "link": article['link'],
                            "published": article['published']
                        })
            except Exception as e:
                logger.error(f"Exception occurred while fetching {url}: {str(e)}")
    
    # Sort by published date and return top 5
    sorted_entries = sorted(entries, key=lambda x: x["published"], reverse=True)
    latest = sorted_entries[:5]
    return [{"title": e["title"], "link": e["link"]} for e in latest] 