import asyncio
import logging
from sqlalchemy import text
from app.core.settings import settings
from app.core.tenant import get_all_tenants, get_tenant_session
from app.core.db import get_master_session
from app.core.llm import analyze_sentiment

logger = logging.getLogger("sentiment-worker")

class SentimentWorker:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)

    async def run(self):
        logger.info("Starting sentiment worker loop...")
        while True:
            try:
                await self.process_cycle()
            except Exception:
                logger.exception("Error in worker loop")
            
            logger.info(f"Sleeping for {settings.POLL_INTERVAL_SECONDS}s")
            await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)

    async def process_cycle(self):
        # 1. Fetch all active tenants
        async for master_session in get_master_session():
            tenants = await get_all_tenants(master_session)
        
        logger.info(f"Found {len(tenants)} active tenants")

        # 2. Process tenants in parallel chunks
        chunk_size = settings.MAX_CONCURRENT_TENANTS
        for i in range(0, len(tenants), chunk_size):
            batch = tenants[i:i + chunk_size]
            await asyncio.gather(*(self.process_tenant(t) for t in batch))

    async def process_tenant(self, t: dict):
        tenant_id = t["tenant_id"]
        logger.info(f"Processing tenant: {tenant_id}")
        # Compute schema name for qualifying tables
        schema = tenant_id.strip().lower() # Use tenant_id directly as schema name
        
        async for session in get_tenant_session(t):
            # 3. Fetch unprocessed interactions
            try:
                query = text(f"""
                    SELECT 
                        raw_json->>'interaction_id' as id,
                        COALESCE(
                            raw_json->>'text', 
                            raw_json->>'message', 
                            raw_json->>'caption', 
                            raw_json->>'comment'
                        ) as text
                    FROM "{schema}".raw_social_interactions
                    WHERE (raw_json->>'interaction_id') NOT IN (
                        SELECT interaction_id FROM "{schema}".sentiment_results
                    )
                    AND COALESCE(
                        raw_json->>'text', 
                        raw_json->>'message', 
                        raw_json->>'caption', 
                        raw_json->>'comment'
                    ) IS NOT NULL
                    LIMIT :limit
                """)
                
                result = await session.execute(query, {"limit": settings.BATCH_SIZE})
                rows = result.fetchall()
                
                if not rows:
                    logger.info(f"No new interactions for tenant {tenant_id}")
                    return

                logger.info(f"Found {len(rows)} interactions to analyze for {tenant_id}")
                
                # 4. Analyze in parallel (limited by semaphore)
                tasks = [self.analyze_and_save(session, schema, row.id, row.text) for row in rows]
                await asyncio.gather(*tasks)
                
                await session.commit()
                logger.info(f"Committed batch for {tenant_id}")

            except Exception:
                logger.exception(f"Failed processing tenant {tenant_id}")
                await session.rollback()

    async def analyze_and_save(self, session, schema, interaction_id, text_content):
        if not text_content:
            return

        async with self.semaphore:
            result = await analyze_sentiment(text_content)
        
        # 5. Save result
        insert_sql = text(f"""
            INSERT INTO "{schema}".sentiment_results (interaction_id, sentiment, emotion, confidence, model_version)
            VALUES (:id, :sentiment, :emotion, :conf, :ver)
            ON CONFLICT (interaction_id) DO NOTHING
        """)
        
        await session.execute(insert_sql, {
            "id": interaction_id,
            "sentiment": result.get("sentiment", "neutral"),
            "emotion": result.get("emotion"),
            "conf": result.get("confidence", 0.0),
            "ver": settings.MODEL_NAME
        })
