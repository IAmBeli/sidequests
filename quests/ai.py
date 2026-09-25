import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from .models import Quest

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class QuestOutput(BaseModel):
    text: str
    difficulty: int
    category: str

def generate_quest():
    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=(
            "Give ease or medium side quest for someone looking to add "
            "variety to their day. Keep the quest text to one or two plain "
            "sentences, no markdown formatting. Category must be exactly "
            " one of: physical, social, creative, exploration, all lowercase."
        ),
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": QuestOutput.model_json_schema()
        },
    )
    result = QuestOutput.model_validate_json(interaction.output_text)
    result.category = result.category.lower()
    quest = Quest.objects.create(
        text=result.text,
        difficulty=result.difficulty,
        category=result.category,
    )
    return quest

def get_embedding(text):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY", output_dimensionality=768)
    )
    return result.embeddings[0].values