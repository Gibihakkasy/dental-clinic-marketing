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

# Optional: import anthropic if available
try:
    import anthropic
except ImportError:
    anthropic = None

# Load API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# Load agents configuration
config_path = os.path.join(os.path.dirname(__file__), 'bots_config.json')
with open(config_path, 'r') as f:
    bot_config = json.load(f)
    agents = bot_config["agents"]

# Logging
logging.basicConfig(level=logging.INFO)

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

@app.get("/bots")
def get_bots():
    # For compatibility with frontend, return agents as bots
    return [{"name": agent["name"], "role": agent["role"]} for agent in agents]

class Message(BaseModel):
    text: str
    conversation_history: List[Dict[str, Any]]
    active_bots: Optional[List[str]] = None

# Unified LLM call
async def call_llm(agent, prompt: str) -> str:
    provider = agent.get("provider")
    model = agent.get("model")
    if provider == "ollama":
        # Import Ollama only if needed
        try:
            from llama_index.core.llms import ChatMessage
            from llama_index.llms.ollama import Ollama
        except ImportError:
            raise Exception("llama_index is not installed. Please install it for Ollama support.")
        llm = Ollama(model=model, request_timeout=120.0)
        response = ""
        for r in llm.stream_chat([ChatMessage(role="user", content=prompt)]):
            response += r.delta
        return response.strip()
    elif provider == "openai":
        if not OPENAI_API_KEY:
            raise Exception("OPENAI_API_KEY not set")
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        if agent["name"] == "Research Agent":
            response = client.responses.create(
                model=model,
                input=prompt,
                tools=[{"type": "web_search"}]
            )
            return response.output_text
        else:
            response = client.responses.create(
                model=model,
                input=prompt
            )
            return response.output_text
    elif provider == "claude":
        if not CLAUDE_API_KEY:
            raise Exception("CLAUDE_API_KEY not set")
        if anthropic is None:
            raise Exception("anthropic package not installed")
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        response = client.messages.create(
            model=model,
            max_tokens=800,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        # Use getattr to avoid attribute errors
        content = getattr(response, 'content', None)
        if content and isinstance(content, list) and hasattr(content[0], 'text'):
            return content[0].text.strip()
        completion = getattr(response, 'completion', None)
        if completion:
            return completion.strip()
        return str(response)
    else:
        raise Exception(f"Unknown provider: {provider}")

def build_prompt(agent, conversation_history: List[Dict[str, Any]], user_message: str) -> str:
    # Custom prompt for each agent
    if agent["name"] == "Research Agent":
        prompt = (
            f"You are a research assistant for a dental clinic's marketing team. "
            f"Your job is to research dental care trends, viral posts, studies, research, or any content in social media. The goal is content that is engaging for potential dental patients. So exclude industry specific information that only interesting for the practitioner."
            f"Always include the source URL for each finding.\n"
        )
        for message in conversation_history:
            if message.get("speaker") == "User":
                prompt += f"User says: '{message['text']}'\n"
        prompt += f"User says: '{user_message}'\n"
        prompt += "Provide a list of 4-5 findings, each with a brief description and a source URL."
        return prompt
    elif agent["name"] == "Planner Agent":
        prompt = (
            f"You are a social media planner for a dental clinic's marketing team."
            f"Your job is to take the Research Agent’s results and creates a detailed Instagram content plan for the upcoming week."
            f"For each post, it includes: the scheduled date, a highly engaging caption tailored for Instagram, a matching image prompt that focuses on realistic Indonesian visuals, and an explanation for the user that connects the post idea back to the original research—helping the user understand the inspiration behind each post.\n"
        )
        for message in conversation_history:
            if message.get("speaker") == "Research Agent":
                prompt += f"Research Agent found: {message['text']}\n"
        prompt += f"User says: '{user_message}'\n"
        prompt += "Create a plan for 1-2 Instagram posts based on the research above."
        return prompt
    else:
        # Fallback
        return user_message

@app.post("/chat")
async def chat(message: Message):
    try:
        user_message = message.text
        conversation_history = message.conversation_history or []
        active_bots = message.active_bots or [agent['name'] for agent in agents]
        responses = []
        bot_responses = []
        for agent in agents:
            if agent['name'] not in active_bots:
                continue
            prompt = build_prompt(agent, conversation_history, user_message)
            logging.info(f"Prompt for {agent['name']}: {prompt}")
            bot_response = await call_llm(agent, prompt)
            bot_responses.append({'speaker': agent['name'], 'text': bot_response})
            responses.append({
                "bot": agent['name'],
                "response": bot_response
            })
        # Optionally update conversation history
        conversation_history.extend(bot_responses)
        return {"responses": responses}
    except Exception as e:
        logging.error(f"Error processing the request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
