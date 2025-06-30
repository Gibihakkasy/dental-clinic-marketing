from dotenv import load_dotenv
load_dotenv()

import os
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import requests
import openai
from bs4 import BeautifulSoup
import feedparser
import datetime
from docx import Document
from fastapi.responses import FileResponse

# Dental news fetching utilities (inlined from fetch_news.py)
import feedparser
import datetime

# Load API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Social Media Planner agent config
AGENT = {
    "name": "Social Media Planner",
    "provider": "openai",
    "model": "gpt-4.1"
}

# RSS feeds
RSS_FEEDS = [
    "http://www.agd.org/myagd/subscriptions/rss/kyt_hottopics.xml",
    "http://www.agd.org/myagd/subscriptions/rss/kyt_factoidweek.xml",
    "http://www.agd.org/myagd/subscriptions/rss/kyt_quiz.xml"
]

def extract_article_text(url: str, max_paragraphs: int = 5) -> str:
    try:
        resp = requests.get(url, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        paragraphs = soup.find_all("p")
        return " ".join(p.get_text().strip() for p in paragraphs[:max_paragraphs])
    except Exception:
        return ""

def fetch_rss_news():
    entries = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed and isinstance(entry.published_parsed, tuple):
                try:
                    published = datetime.datetime(*entry.published_parsed[:6])
                except Exception:
                    published = datetime.datetime.now()
            else:
                published = datetime.datetime.now()
            entries.append({
                "title": entry.get("title"),
                "link": entry.get("link"),
                "published": published
            })
    sorted_entries = sorted(entries, key=lambda x: x["published"], reverse=True)
    latest = sorted_entries[:5]
    return [{"title": e["title"], "link": e["link"]} for e in latest]

# FastAPI app setup
app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SummarizeRequest(BaseModel):
    user_message: Optional[str] = None

@app.get("/bots")
def get_bots():
    return [{"name": AGENT["name"], "role": "Creates Instagram content plan from latest dental news."}]

@app.post("/generate_social_plan")
async def generate_social_plan(request: SummarizeRequest):
    try:
        if not OPENAI_API_KEY:
            raise Exception("OPENAI_API_KEY not set")
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        rss_items = fetch_rss_news()
        summaries = []
        for item in rss_items:
            article_text = extract_article_text(item["link"])
            summary_prompt = (
                f"Summarize the following dental news article for dentists audience in Bahasa Indonesia.\n"
                f"Title: {item['title']}\n"
                f"URL: {item['link']}\n"
                f"Content: {article_text}\n"
                f"Return a concise summary."
            )
            # Use OpenAI response API with web search tools for richer summaries
            summary_resp = client.responses.create(
                model=AGENT["model"],
                input=summary_prompt,
                tools=[{"type": "web_search"}]
            )
            summary = getattr(summary_resp, 'output_text', None)
            if summary:
                summary = summary.strip()
            else:
                summary = "(No summary returned)"
            summaries.append({
                "title": item["title"],
                "url": item["link"],
                "summary": summary
            })
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        doc_filename = f"social_plan_{now}.docx"
        # Ensure the 'documents' directory exists at project root
        documents_dir = os.path.join(os.getcwd(), "documents")
        os.makedirs(documents_dir, exist_ok=True)
        doc_path = os.path.join(documents_dir, doc_filename)
        doc = Document()
        doc.add_heading("Dental Clinic Social Media Content Plan", 0)
        doc.add_paragraph(f"Generated: {now}")
        for idx, item in enumerate(summaries, 1):
            doc.add_heading(f"{idx}. {item['title']}", level=1)
            doc.add_paragraph(f"URL: {item['url']}")
            doc.add_paragraph(f"Summary: {item['summary']}")
            caption_prompt = (
                f"Given this summary of a dental news article, write a highly engaging Instagram caption for a dental clinic's patients in BahasaIndonesia.\n"
                f"Summary: {item['summary']}\n"
                f"Caption:"
            )
            caption_resp = client.chat.completions.create(
                model=AGENT["model"],
                messages=[{"role": "user", "content": caption_prompt}]
            )
            caption = getattr(caption_resp.choices[0].message, 'content', None)
            if caption:
                caption = caption.strip()
            else:
                caption = "(No caption returned)"
            image_prompt_prompt = (
                f"Given this summary, write a prompt for an image generation AI to create an image for a dental clinic instagram post. The audience is potential patient of an Indonesian dental clinic.\n"
                f"Summary: {item['summary']}\n"
                f"Image Prompt:"
            )
            image_prompt_resp = client.chat.completions.create(
                model=AGENT["model"],
                messages=[{"role": "user", "content": image_prompt_prompt}]
            )
            image_prompt = getattr(image_prompt_resp.choices[0].message, 'content', None)
            if image_prompt:
                image_prompt = image_prompt.strip()
            else:
                image_prompt = "(No image prompt returned)"
            doc.add_heading("Instagram Content", level=2)
            doc.add_paragraph(f"Caption: {caption}")
            doc.add_paragraph(f"Image Prompt: {image_prompt}")
        doc.save(doc_path)
        return {"file": doc_filename}
    except Exception as e:
        logging.error(f"Error generating social plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join("backend", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=filename)
