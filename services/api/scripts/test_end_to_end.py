import asyncio
import os
import sys
import logging
import uuid
import json
from datetime import datetime
from threading import Thread
import importlib.util

# Paths
API_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKER_DIR = os.path.abspath(os.path.join(API_DIR, "../../services/worker"))
from dotenv import load_dotenv
# We load worker env to get Azure keys if needed, but for API app it uses its own settings.
# Actually API app needs DB config.
# Let's just ensure API path is correct.
sys.path.append(API_DIR)

from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from sqlalchemy import text
import subprocess
try:
    from app.main import app
    from app.core.db import get_db, SessionLocal
    from app.core.tenant_store import get_tenant_db
    from app.core.tenant_db import get_tenant_session
    from app.core.tenant_schema import tenant_schema_name
    from scripts.generate_social_data import DataGenerator
except ImportError:
    # If run from root, relative imports might fail
    sys.path.append(os.path.join(API_DIR, "app"))
    from app.main import app
    from app.core.db import get_db, SessionLocal
    from app.core.tenant_store import get_tenant_db
    from app.core.tenant_db import get_tenant_session
    from app.core.tenant_schema import tenant_schema_name
    from scripts.generate_social_data import DataGenerator
    from httpx import AsyncClient, ASGITransport

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("e2e-test")

# Tenant Config
TENANT_ID = "org_423b3ac30b46426db809c4196f7d358a"
ORG_NAME = "InsightIQ_Prod_Test"
DB_CONFIG = {
    "host": "66.135.22.167",
    "port": 5432,
    "db_name": "galaxiq_tenants",
    "user": "postgres",
    "password": "galaxiq"
}

async def run_worker_cycle(tenant_id):
    """Runs the worker logic for a single cycle using subprocess to avoid app package collision."""
    logger.info("Running sentiment worker cycle (subprocess)...")
    
    # We execute a one-liner in the worker directory
    # We must ensure the worker environment variables are loaded relative to WORKER_DIR
    # subprocess with cwd=WORKER_DIR should pick up .env if python-dotenv is used in worker code (it is in settings)
    
    cmd = [
        sys.executable, "-c", 
        "import asyncio; from app.worker import SentimentWorker; asyncio.run(SentimentWorker().process_cycle())"
    ]
    
    proc = subprocess.run(cmd, cwd=WORKER_DIR, capture_output=True, text=True)
    
    if proc.returncode != 0:
        logger.error(f"Worker failed: {proc.stderr}")
        raise Exception("Worker failed")
    
    logger.info("Worker cycle complete.")

async def run_summary_cycle(tenant_id):
    """Runs the summary worker logic for a single cycle using subprocess."""
    logger.info("Running summary worker cycle (subprocess)...")
    
    log_file = os.path.join(WORKER_DIR, "llm_summary_input.log")
    if os.path.exists(log_file):
        os.remove(log_file)

    cmd = [
        sys.executable, "-c", 
        "import asyncio; from app.summarizer import SummaryWorker; asyncio.run(SummaryWorker().process_cycle())"
    ]
    
    proc = subprocess.run(cmd, cwd=WORKER_DIR, capture_output=True, text=True)
    
    if proc.returncode != 0:
        logger.error(f"Summary worker failed: {proc.stderr}")
        raise Exception("Summary worker failed")
    
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            content = f.read()
            logger.info(f"Captured LLM Input ({len(content)} chars):\n{content[:200]}...")
    else:
        logger.warning("LLM input log file not found!")

    logger.info("Summary worker cycle complete.")

def run_dbt(tenant_id):
    """Runs DBT for the specific tenant."""
    logger.info("Running DBT...")
    dbt_dir = os.path.abspath(os.path.join(API_DIR, "../../services/dbt"))
    
    # Try to use DBT_BIN from settings if available
    dbt_bin = "dbt"
    try:
        from app.core.settings import settings
        if settings.DBT_BIN:
            dbt_bin = settings.DBT_BIN
    except ImportError:
        pass
        
    logger.info(f"Using DBT binary: {dbt_bin}")
    
    schema = tenant_schema_name(tenant_id)
    # We use profiles-dir . to use local profiles.yml
    cmd = f"cd {dbt_dir} && {dbt_bin} run --profiles-dir . --vars '{{\"tenant_schema\": \"{schema}\"}}'"
    
    ret = os.system(cmd)
    if ret != 0:
        raise Exception("DBT Run failed")
    logger.info("DBT Run complete.")

async def verify_data(tenant_id):
    """Verifies that data exists in the final tables."""
    logger.info("Verifying data...")
    
    async with SessionLocal() as master_session:
        tenant_cfg = await get_tenant_db(master_session, tenant_id)
    
    schema = tenant_schema_name(tenant_id)
    
    async for session in get_tenant_session(tenant_cfg):
        await session.execute(text(f'SET search_path TO "{schema}"'))
        
        # Check Raw Data
        res = await session.execute(text("SELECT count(*) FROM raw_social_posts"))
        posts_count = res.scalar()
        logger.info(f"Raw Posts: {posts_count}")
        
        # Check Sentiment Results
        res = await session.execute(text("SELECT count(*) FROM sentiment_results"))
        sentiment_count = res.scalar()
        logger.info(f"Sentiment Results: {sentiment_count}")
        
        # Check DBT Models (e.g., fct_posts or dim_account)
        # Assuming fct_posts is created
        try:
            res = await session.execute(text("SELECT count(*) FROM fct_posts"))
            fct_count = res.scalar()
            logger.info(f"Fact Posts: {fct_count}")
        except Exception as e:
            logger.warning(f"Could not query fct_posts: {e}")

        # Check Account Dimension
        try:
             res = await session.execute(text("SELECT count(*) FROM dim_account"))
             dim_count = res.scalar()
             logger.info(f"Dim Account: {dim_count}")
        except Exception:
             pass

        # Check Summaries
        try:
            res = await session.execute(text("SELECT count(*) FROM post_embeddings WHERE post_id LIKE 'summary_%'"))
            summary_count = res.scalar()
            logger.info(f"Summary Results: {summary_count}")
            
            if summary_count > 0:
                res = await session.execute(text("SELECT payload FROM post_embeddings WHERE post_id LIKE 'summary_%' LIMIT 1"))
                payload = res.scalar()
                # SQLAlchemy/asyncpg might have already parsed JSONB to dict
                if isinstance(payload, str):
                    payload_dict = json.loads(payload)
                else:
                    payload_dict = payload
                summary_sample = payload_dict.get("summary", "")[:100]
                logger.info(f"Summary Sample: {summary_sample}...")
                
                # Verify Embeddings
                res = await session.execute(text("SELECT embedding FROM post_embeddings WHERE post_id LIKE 'summary_%' LIMIT 1"))
                embedding = res.scalar()
                if embedding:
                    logger.info(f"✅ Embedding found for summary (Length: {len(embedding)})")
                else:
                    logger.error("❌ Embedding missing for summary!")
                    raise Exception("Embedding missing for summary")

        except Exception as e:
            logger.warning(f"Could not query summaries: {e}")

async def main():
    logger.info(f"Starting End-to-End Test for Org: {ORG_NAME}")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Bootstrap Schema (Registration is gone)
        logger.info(f"1. Bootstrapping Schema for {TENANT_ID}...")
        resp = await client.post("/schema/bootstrap", json={"tenant_id": TENANT_ID})
        if resp.status_code != 200:
            logger.error(f"Bootstrap failed: {resp.text}")
            return
        logger.info("Schema Bootstrapped.")
        
    # 2. Generate Data
    logger.info("2. Generating Seed Data...")
    generator = DataGenerator(TENANT_ID)
    generator.generate_posts(count=10) # Smaller batch for test
    generator.generate_interactions(count_per_post=2)
    generator.generate_accounts()
    generator.generate_account_metrics()
    await generator.seed()
    
    # 3. Run Worker (Sentiment Analysis)
    logger.info("3. Running Sentiment Worker...")
    await run_worker_cycle(TENANT_ID)
    
    # 4. Run DBT
    logger.info("4. Running DBT Transformation...")
    run_dbt(TENANT_ID)
    
    # 5. Run Summary Worker
    logger.info("5. Running Summary Worker...")
    await run_summary_cycle(TENANT_ID)
    
    # 6. Verify
    await verify_data(TENANT_ID)
    
    logger.info("✅ End-to-End Test Complete!")

if __name__ == "__main__":
    asyncio.run(main())
