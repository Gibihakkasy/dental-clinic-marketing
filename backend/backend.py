from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from llama_index.core.llms import ChatMessage
from llama_index.llms.ollama import Ollama
from typing import Optional
import logging
import json
import os

# Get the absolute path of the bots_config.json file relative to this script
config_path = os.path.join(os.path.dirname(__file__), 'bots_config.json')

# Load bots configuration from external JSON file
with open(config_path, 'r') as f:
    bot_config = json.load(f)
    characters = bot_config["characters"]

# Dynamically create bot variables
bots = []
for idx, character in enumerate(characters, start=1):
    bots.append({
        "name": character['name'],
        "model": character['model'],
        "personality": character['personality']
    })

# Configuration du logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Définir les origines autorisées pour CORS
origins = [
    "http://localhost:3000",  # Origine de l'application React
    "http://127.0.0.1:3000",  # Variante avec l'adresse IP
]

# Ajouter le middleware CORS pour permettre les requêtes de l'interface React
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Origines autorisées
    allow_credentials=True,
    allow_methods=["*"],  # Autoriser toutes les méthodes (GET, POST, etc.)
    allow_headers=["*"],  # Autoriser tous les en-têtes
)

@app.get("/bots")
def get_bots():
    return bots

async def generate_response(model_name: str, prompt: str) -> str:
    """
    Fonction pour générer une réponse à partir d'un modèle Ollama.
    """
    try:
        llm = Ollama(model=model_name, request_timeout=120.0)
        response = ""
        # Utiliser un itérable synchronisé
        for r in llm.stream_chat([ChatMessage(role="user", content=prompt)]):
            response += r.delta
        return response.strip()

    except Exception as e:
        logging.error(f"Erreur avec le modèle {model_name}: {str(e)}")
        raise e

def build_prompt(bot_name: str, personality: str, conversation_history: List[Dict[str, Any]]) -> str:
    """
    Build a prompt for the bot using the full conversation history and its personality.
    """
    prompt = f"You are {bot_name}, {personality}.\n"

    for message in conversation_history:
        if 'speaker' in message and 'text' in message:
            speaker = message['speaker']
            text = message['text']
            prompt += f"{speaker} says: '{text}'\n"

    prompt += "Respond without using asterisks to indicate actions or non-verbal cues, and in a way that stays true to your personality and reflects a realistic, dynamic conversation as if you were participating in a casual group chat."
    return prompt



class Message(BaseModel):
    text: str
    conversation_history: List[Dict[str, Any]]
    active_bots: Optional[List[str]] = None  # New field for active bots


@app.post("/chat")
async def chat(message: Message):
    try:
        user_message = message.text
        conversation_history = message.conversation_history or []
        active_bots = message.active_bots or [bot['name'] for bot in bots]  # Default to all bots if none specified

        # Log the received conversation history
        logging.info(f"Conversation history received: {conversation_history}")

        # **Ensure we add the user's message only once**
        valid_conversation_history = [
            msg for msg in conversation_history
            if isinstance(msg, dict) and "speaker" in msg and "text" in msg
        ]

        # Append the user's message to the conversation history **only once** 
        if not valid_conversation_history or valid_conversation_history[-1]["speaker"] != "User":
            valid_conversation_history.append({"speaker": "User", "text": user_message})

        responses = []
        bot_responses = []

        for bot in bots:
            if bot['name'] not in active_bots:
                continue

            bot_name = bot['name']
            model_name = bot['model']
            personality = bot['personality']

            prompt = build_prompt(bot_name, personality, valid_conversation_history)
            logging.info(f"Prompt generated for {bot_name}: {prompt}")
            bot_response = await generate_response(model_name, prompt)

            bot_responses.append({'speaker': bot_name, 'text': bot_response})
            responses.append({
                "bot": bot_name,
                "response": bot_response
            })

        # Update conversation history with bot responses
        valid_conversation_history.extend(bot_responses)

        # Return responses and updated conversation history if needed
        return {
            "responses": responses,
            # Optionally return the updated conversation history
            # "conversation_history": valid_conversation_history
        }

    except Exception as e:
        logging.error(f"Error processing the request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
