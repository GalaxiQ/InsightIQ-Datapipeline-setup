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

SUMMARY_PROMPT = """
You are a senior data analyst. 
Your task is to summarize changes in analytical data into a brief, detailed essay.
Include as much detail as possible about performance shifts, sentiment trends, and account growth.
Maintain a professional and insightful tone.
"""

TABLE_SUMMARY_PROMPT = """
You are a senior data analyst. 
Summarize the changes for the specific table provided. 
Focus on specific metrics, row counts, and notable updates.
Keep it concise but informative.
"""

COLLATE_PROMPT = """
You are a senior data analyst. 
You are given multiple individual table summaries. 
Your task is to synthesize these into one comprehensive, high-level "essay" summary.
Highlight cross-table insights and overall trends.
Maintain a professional and insightful tone.
"""

async def generate_detailed_summary(change_data: str) -> str:
    try:
        response = await client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": SUMMARY_PROMPT},
                {"role": "user", "content": f"Analyze these changes:\n{change_data}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        return f"Error generating summary: {str(e)}"

async def generate_table_summary(table_name: str, change_data: str) -> str:
    try:
        response = await client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": TABLE_SUMMARY_PROMPT},
                {"role": "user", "content": f"Table: {table_name}\nChanges:\n{change_data}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Table summary failed for {table_name}: {e}")
        return f"Error summarizing {table_name}: {str(e)}"

async def generate_embeddings(text: str) -> list[float]:
    try:
        response = await client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return []

