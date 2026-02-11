from openai import AsyncAzureOpenAI
from app.core.settings import settings
import json
import logging

logger = logging.getLogger("worker-llm")

client = AsyncAzureOpenAI(
    api_key=settings.AZURE_OPENAI_API_KEY,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
)

SYSTEM_PROMPT = """
You are an expert social media sentiment analyst. 
Analyze the following text and extract:
1. Sentiment: strictly 'positive', 'neutral', or 'negative'.
2. Emotion: one word describing the emotion (e.g., trust, excitement, frustration, anger, joy).
3. Confidence: a float between 0.0 and 1.0.

Return the result as a valid JSON object with keys: "sentiment", "emotion", "confidence".
"""

async def analyze_sentiment(text: str) -> dict:
    try:
        response = await client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Text: {text}"}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        return {"sentiment": "neutral", "emotion": "unknown", "confidence": 0.0, "error": str(e)}
