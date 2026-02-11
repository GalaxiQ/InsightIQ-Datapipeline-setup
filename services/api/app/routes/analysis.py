import json
import logging
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy import text
from openai import AsyncAzureOpenAI
import openai

from app.core.db import get_db
from app.core.settings import settings
from app.models.analysis import SummarizeRequest

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Azure OpenAI Client
# We use AsyncAzureOpenAI for non-blocking calls
client = AsyncAzureOpenAI(
    api_key=settings.AZURE_OPENAI_API_KEY,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
)

async def generate_summary(content: str, prompt_instruction: str) -> str:
    """Helper to generate summary using Chat Completion"""
    try:
        response = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant.",
                },
                {
                    "role": "user",
                    "content": f"{prompt_instruction}\n\nInput Data:\n{content}",
                }
            ],
            max_completion_tokens=16384,
            model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}")

async def generate_embedding(text_content: str) -> List[float]:
    """Helper to generate embedding"""
    try:
        response = await client.embeddings.create(
            input=[text_content],
            model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
        )
        # response.data[0].embedding
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")

@router.post("/summarize")
async def summarize_and_store(
    req: SummarizeRequest,
    x_tenant_id: str = Header(..., description="Tenant ID"),
    master_db=Depends(get_db)
):
    """
    Takes JSON input, generates two summaries, combines them with date/time,
    creates an embedding, and stores it in post_embeddings in the tenant's schema.
    """
    try:
        # Resolve Tenant
        from app.core.tenant_store import get_tenant_db
        from app.core.tenant_schema import qualified_table, tenant_schema_name
        from app.core.tenant_db import get_tenant_session

        try:
            cfg = await get_tenant_db(master_db, x_tenant_id)
            schema = tenant_schema_name(x_tenant_id)
            table_name = qualified_table(schema, "post_embeddings")
        except Exception:
            raise HTTPException(401, "Invalid tenant")

        # 1. Prepare Input
        # Serialize payload to string for LLM
        payload_str = json.dumps(req.payload, default=str)
        
        # 2. Generate Summaries
        # First Summary: Broad summary
        summary_1 = await generate_summary(
            payload_str, 
            "Create a detailed summary info of all the social media handle details provided for the company. The summary should have every detail especially in terms of nos and overall context, it should capture every possible information which will be important for executives of that company."
        )
        
        # Second Summary: "summarize the json output" (interpreted as structure/highlights)
        summary_2 = await generate_summary(
            payload_str, 
            "Summarize the provided JSON output data structure and content highlights. Capture the numbers,scores, issues, recommendations, etc whichever is important and relevant for the company to know and grow. IT should have every detailed information about each KPIs. The summary should be very detailed and should capture every possible information which will be important for executives of that company."
        )
        
        # 3. Combine Summaries
        current_time_str = datetime.now().isoformat()
        combined_text = (
            f"Date: {current_time_str}\n\n"
            f"Summary 1:\n{summary_1}\n\n"
            f"Summary 2:\n{summary_2}\n\n"
            f"Original Content Context: Summary of input."
        )
        
        # 4. Generate Embedding for Combined Text
        embedding_vector = await generate_embedding(combined_text)
        payload_json = json.dumps(
            {
                "combined_text": combined_text
            }
        )
        # 5. Store in Database
        post_id = str(uuid.uuid4())
        
        # We need to format vector for SQL. 
        # For pgvector with sqlalchemy/asyncpg, passing a list often works if the driver supports it, 
        # OR we pass a string representation '[x,y,z]'.
        embedding_str = f"[{','.join(map(str, embedding_vector))}]"
        
        sql = f"""
        INSERT INTO {table_name} (post_id, embedding, payload, created_at)
        VALUES (:post_id, :embedding, CAST(:payload AS jsonb), NOW())
        """
        
        async for db in get_tenant_session(cfg):
            try:
                await db.execute(
                    text(sql),
                    {
                        "post_id": post_id,
                        "embedding": embedding_str, 
                        "payload": payload_json
                    }
                )
                await db.commit()
            except Exception as inner_e:
                await db.rollback()
                logger.error(f"DB Insert failed: {inner_e}")
                raise HTTPException(500, f"Database insertion failed: {str(inner_e)}")
        
        return {
            "status": "ok", 
            "post_id": post_id,
            "created_at": current_time_str
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Analysis failed")
        raise HTTPException(status_code=500, detail=str(e))
