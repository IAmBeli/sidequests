import os
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

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
    quest = QuestOutput.model_validate_json(interaction.output_text)
    quest.category = quest.category.lower()
    return quest