import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)

import os

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
            
        self._init_db()

    def _init_db(self):
        """Initialize the database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    link TEXT UNIQUE NOT NULL,
                    summary TEXT,
                    caption TEXT,
                    image_prompt TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def get_article(self, link: str) -> Optional[Dict[str, Any]]:
        """Get a cached article by its link."""
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

# Create a singleton instance
cache = ArticleCache()
