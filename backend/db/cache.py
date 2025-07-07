import os
import sqlite3
import json
import hashlib
import pickle
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
import logging

# Set up logging
logger = logging.getLogger(__name__)

def get_topic_key(topic: str) -> str:
    """Generate a consistent cache key for a topic"""
    return f"topic_{hashlib.md5(topic.lower().encode()).hexdigest()}"

class ArticleCache:
    def __init__(self, db_path: str | None = None):
        """Initialize the cache database."""
        if db_path is None:
            # Default to a data directory in the project root
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, 'article_cache.db')
        else:
            self.db_path = db_path
            
        # Initialize the database
        self._init_db()

    def _init_db(self):
        """Initialize the database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Articles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    link TEXT PRIMARY KEY,
                    title TEXT,
                    summary TEXT,
                    caption TEXT,
                    image_prompt TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            ''')
            
            # Topics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS topics (
                    id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    caption TEXT NOT NULL,
                    image_prompt TEXT NOT NULL,
                    sources TEXT,  -- JSON array of sources
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def get_article(self, link: str) -> Optional[Dict[str, Any]]:
        """Get a cached article by its link."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM articles 
                    WHERE link = ?
                ''', (link,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        except sqlite3.OperationalError as e:
            logger.error(f"Error getting article: {str(e)}")
            return None

    def save_article(self, article: Dict[str, Any]) -> int | None:
        """Save or update an article in the cache."""
        existing = self.get_article(article['link'])
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if existing:
                # Update existing article
                cursor.execute('''
                    UPDATE articles 
                    SET title = ?, 
                        summary = ?, 
                        caption = ?, 
                        image_prompt = ?,
                        updated_at = ?
                    WHERE link = ?
                ''', (
                    article.get('title', ''),
                    article.get('summary', ''),
                    article.get('caption', ''),
                    article.get('image_prompt', ''),
                    now,
                    article['link']
                ))
                return cursor.lastrowid
            else:
                # Insert new article
                cursor.execute('''
                    INSERT INTO articles 
                    (title, link, summary, caption, image_prompt, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article.get('title', ''),
                    article['link'],
                    article.get('summary', ''),
                    article.get('caption', ''),
                    article.get('image_prompt', ''),
                    now,
                    now
                ))
                return cursor.lastrowid

    # Topic management methods
    def save_topic(self, topic_data: Dict[str, Any]) -> str:
        """Save or update a topic in the cache."""
        topic_id = get_topic_key(topic_data['topic'])
        data = {
            'id': topic_id,
            'topic': topic_data['topic'],
            'summary': topic_data.get('summary', ''),
            'caption': topic_data.get('caption', ''),
            'image_prompt': topic_data.get('image_prompt', ''),
            'sources': json.dumps(topic_data.get('sources', [])),
            'created_at': topic_data.get('created_at', datetime.utcnow().timestamp())
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO topics (id, topic, summary, caption, image_prompt, sources, created_at)
                VALUES (:id, :topic, :summary, :caption, :image_prompt, :sources, :created_at)
            ''', data)
            conn.commit()
            
        return topic_id
    
    def get_topic(self, topic_id: str) -> Optional[Dict[str, Any]]:
        """Get a topic by its ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM topics WHERE id = ?', (topic_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row['id'],
                    'topic': row['topic'],
                    'summary': row['summary'],
                    'caption': row['caption'],
                    'image_prompt': row['image_prompt'],
                    'sources': json.loads(row['sources']) if row['sources'] else [],
                    'created_at': row['created_at']
                }
            return None
    
    def list_topics(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all topics with pagination."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, topic, summary, created_at 
                FROM topics 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            topics = []
            for row in cursor.fetchall():
                topics.append({
                    'id': row['id'],
                    'topic': row['topic'],
                    'preview': (row['summary'] or '')[:100] + ('...' if len(row['summary'] or '') > 100 else ''),
                    'created_at': row['created_at']
                })
            return topics
    
    def delete_topic(self, topic_id: str) -> bool:
        """Delete a topic by its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM topics WHERE id = ?', (topic_id,))
            conn.commit()
            return cursor.rowcount > 0
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT data FROM cache WHERE key = ?', (key,))
                row = cursor.fetchone()
                if row:
                    return pickle.loads(row['data'])
                return default
        except sqlite3.OperationalError:
            # Table might not exist yet
            return default
            
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Set a value in the cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create cache table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cache (
                        key TEXT PRIMARY KEY,
                        data BLOB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP
                    )
                ''')
                
                # Serialize the value
                serialized = sqlite3.Binary(pickle.dumps(value))
                
                # Calculate expiration time if provided
                expires_at = None
                if expire is not None:
                    expires_at = datetime.utcnow().timestamp() + expire
                
                # Insert or update the cache entry
                cursor.execute('''
                    INSERT OR REPLACE INTO cache (key, data, expires_at)
                    VALUES (?, ?, ?)
                ''', (key, serialized, expires_at))
                
                # Clean up expired entries
                cursor.execute('DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?', 
                             (datetime.utcnow().timestamp(),))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Error setting cache value for key {key}: {str(e)}")
            raise

# Create a singleton instance
cache = ArticleCache()
