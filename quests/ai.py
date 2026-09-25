import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from .models import Quest
from datetime import timedelta
from django.utils import timezone
from pgvector.django import CosineDistance

SIMILARITY_WINDOW_DAYS = 7
SIMILARITY_TRESHOLD = 0.15

MAX_GENERATION_ATTEMPTS = 3

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class QuestOutput(BaseModel):
    text: str
    difficulty: int
    category: str

def generate_quest(user):
    for _ in range(MAX_GENERATION_ATTEMPTS):
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

        embedding = get_embedding(result.text)
        if not is_too_similar(user, embedding):
            break

    return Quest.objects.create(
        text=result.text,
        difficulty=result.difficulty,
        category=result.category,
        embedding=embedding,
    )


def get_embedding(text):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY", output_dimensionality=768)
    )
    return result.embeddings[0].values

def is_too_similar(user, embedding):
    since = timezone.now() - timedelta(days=SIMILARITY_WINDOW_DAYS)

    recent_quests = Quest.objects.filter(
        assignment__user=user,
        assignment__taken_at__gte=since,
        embedding__is_null=False,
    )

    return recent_quests.annotate(distance=CosineDistance("embedding", embedding)).filter(distance__lt=SIMILARITY_TRESHOLD).exists()