import asyncio
import logging
import json
from datetime import datetime
from sqlalchemy import text
from app.core.settings import settings
from app.core.tenant import get_all_tenants, get_tenant_session
from app.core.db import get_master_session
from app.core.llm import generate_table_summary, generate_embeddings

logger = logging.getLogger("summary-worker")

class SummaryWorker:
    def __init__(self):
        pass

    async def process_cycle(self):
        async for master_session in get_master_session():
            tenants = await get_all_tenants(master_session)
        
        logger.info(f"Found {len(tenants)} active tenants for summarization")

        for t in tenants:
            await self.process_tenant(t)

    async def process_tenant(self, t: dict):
        tenant_id = t["tenant_id"]
        schema = tenant_id.strip().lower() # Use tenant_id directly as schema name
        
        async for session in get_tenant_session(t):
            try:
                # 1. Get last checkpoint
                checkpoint_query = text(f'SELECT last_summarized_at FROM "{schema}".summary_checkpoint ORDER BY last_summarized_at DESC LIMIT 1')
                res = await session.execute(checkpoint_query)
                row = res.fetchone()
                last_ts = row[0] if row else datetime(2000, 1, 1)

                logger.info(f"Last summary for {tenant_id} at {last_ts}")

                # 2. Discover Tables
                discover_query = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = :schema 
                    AND table_name NOT IN ('post_embeddings', 'summary_checkpoint', 'raw_events')
                """)
                res = await session.execute(discover_query, {"schema": schema})
                tables = [r[0] for r in res.fetchall()]
                
                partial_summaries = []
                all_raw_changes = []
                
                # 3. Summarize each table individually
                for table in tables:
                    columns_query = text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = :schema AND table_name = :table
                    """)
                    res = await session.execute(columns_query, {"schema": schema, "table": table})
                    cols = [r[0] for r in res.fetchall()]
                    
                    ts_col = None
                    for candidate in ['last_updated', 'processed_at', 'fetched_at', 'ingested_at', 'snapshot_time', 'created_at']:
                        if candidate in cols:
                            ts_col = candidate
                            break
                    
                    if not ts_col:
                        continue

                    # Fetch changed rows
                    change_query = text(f'SELECT * FROM "{schema}"."{table}" WHERE {ts_col} > :ts LIMIT 50')
                    res = await session.execute(change_query, {"ts": last_ts})
                    rows = res.fetchall()
                    
                    if rows:
                        logger.info(f"Found {len(rows)} changes in {table}, summarizing...")
                        table_changes = []
                        for r in rows:
                            row_data = ", ".join([f"{cols[i]}={r[i]}" for i in range(len(cols)) if i < len(r)])
                            table_changes.append(row_data)
                        
                        raw_table_data = "\n".join(table_changes)
                        all_raw_changes.append(f"--- Table: {table} ---\n{raw_table_data}")
                        
                        # Partial summary for this table
                        partial = await generate_table_summary(table, raw_table_data)
                        partial_summaries.append(f"### Table: {table}\n{partial}")

                if not partial_summaries:
                    logger.info(f"No new changes for {tenant_id}")
                    return

                # 4. Concatenate all partial summaries
                logger.info(f"Concatenating {len(partial_summaries)} table summaries for {tenant_id}")
                final_summary = "\n\n".join(partial_summaries)
                
                # 5. Generate Embeddings for the concatenated string
                logger.info(f"Generating embeddings for final summary...")
                embedding_vector = await generate_embeddings(final_summary)
                
                # Log raw changes for audit
                with open("llm_summary_input.log", "w") as f:
                    f.write("\n\n".join(all_raw_changes))
                
                # 6. Store result
                summary_id = f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                insert_sql = text(f"""
                    INSERT INTO "{schema}".post_embeddings (post_id, payload, embedding)
                    VALUES (:id, :payload, :embedding)
                """)
                await session.execute(insert_sql, {
                    "id": summary_id,
                    "payload": json.dumps({
                        "summary": final_summary, 
                        "partial_summaries": partial_summaries,
                        "type": "global_daily", 
                        "source_tables_count": len(partial_summaries)
                    }),
                    "embedding": str(embedding_vector) if embedding_vector else None
                })
                
                # 7. Update checkpoint
                checkpoint_sql = text(f'INSERT INTO "{schema}".summary_checkpoint (last_summarized_at, summary_type) VALUES (now(), :type)')
                await session.execute(checkpoint_sql, {"type": "global_daily"})
                
                await session.commit()
                logger.info(f"Generated and saved final concatenated summary and embeddings for {tenant_id}")

            except Exception:
                logger.exception(f"Failed summary for {tenant_id}")
                await session.rollback()
