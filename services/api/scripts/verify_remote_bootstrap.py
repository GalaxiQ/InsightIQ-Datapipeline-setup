import asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import sys
import os

# Configuration
API_URL = "http://localhost:8000"
TENANT_ID = "org_423b3ac30b46426db809c4196f7d358a"
DB_URL = "postgresql+asyncpg://postgres:galaxiq@66.135.22.167:5432/galaxiq_tenants"

async def check_tables(schema):
    print(f"Checking tables in schema: {schema}")
    engine = create_async_engine(DB_URL)
    async with engine.connect() as conn:
        query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = :schema
        """)
        res = await conn.execute(query, {"schema": schema})
        tables = [row[0] for row in res.fetchall()]
        print(f"Found tables: {tables}")
        return tables

async def main():
    print(f"--- Verifying /bootstrap for {TENANT_ID} ---")
    
    # 1. Call Bootstrap Endpoint
    async with httpx.AsyncClient() as client:
        try:
            print(f"Calling {API_URL}/schema/bootstrap...")
            resp = await client.post(
                f"{API_URL}/schema/bootstrap", 
                json={"tenant_id": TENANT_ID},
                timeout=30.0
            )
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.json()}")
            
            if resp.status_code == 200:
                print("✅ Bootstrap endpoint successful.")
            elif resp.status_code == 404:
                print(f"❌ Schema {TENANT_ID} not found in database.")
                return
            else:
                print(f"❌ Bootstrap failed with status {resp.status_code}")
                return
        except Exception as e:
            print(f"❌ Error calling API: {e}")
            print("Note: Ensure the API server is running at localhost:8000")
            return

    # 2. Verify tables in DB
    tables = await check_tables(TENANT_ID)
    required_tables = [
        "raw_social_posts", 
        "raw_social_interactions", 
        "raw_account_metrics", 
        "fct_posts", 
        "dim_account"
    ]
    
    missing = [t for t in required_tables if t not in tables]
    if not missing:
        print("✅ All required tables exist.")
    else:
        print(f"❌ Missing tables: {missing}")

if __name__ == "__main__":
    asyncio.run(main())
