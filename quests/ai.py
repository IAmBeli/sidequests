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

BASE_PROMPT = (
    "Give {difficulty_text} side quest for someone looking to add "
    "variety to their day. Keep the quest text to one or two plain "
    "sentences, no markdown formatting. Category must be exactly "
    "one of: physical, social, creative, exploration, all lowercase."
)

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class QuestOutput(BaseModel):
    text: str
    difficulty: int
    category: str

def build_prompt(recent_texts, difficulty=None):
    if difficulty is None:
        difficulty_text = "an easy or medium"
    else:
        label = dict(Quest.DIFFICULTY_CHOICES)[difficulty].lower()
        difficulty_text = f"a {label} (on a scale from very easy to very hard)"
    prompt = BASE_PROMPT.format(difficulty_text=difficulty_text)
    if not recent_texts:
        return prompt
    history =  "\n".join(f"- {text}" for text in recent_texts)
    return (
        f"{BASE_PROMPT}\n\n"
        "The user recently recieved these quests. Suggest something "
        "clearly different in idea and activity, not a rephrasing of "
        f"any of them:\n{history}"
    )

def generate_quest(user, difficulty=None):
    recent_texts = list(get_recent_quests(user).values_list("text", flat=True))

    for _ in range(MAX_GENERATION_ATTEMPTS):
        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            input=build_prompt(recent_texts, difficulty),
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": QuestOutput.model_json_schema()
            },
        )
        result = QuestOutput.model_validate_json(interaction.output_text)
        result.category = result.category.lower()

        if difficulty is not None:
            result.difficulty = difficulty

        embedding = get_embedding(result.text)
        if not is_too_similar(user, embedding):
            break
        recent_texts.append(result.text)

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
    return get_recent_quests(user).filter(
        embedding__isnull=False,
    ).annotate(
        distance=CosineDistance("embedding", embedding)
    ).filter(distance__lt=SIMILARITY_TRESHOLD).exists()

def get_recent_quests(user):
    since = timezone.now() - timedelta(days=SIMILARITY_WINDOW_DAYS)
    return Quest.objects.filter(
        assignments__user=user,
        assignments__taken_at__gte=since,
    )