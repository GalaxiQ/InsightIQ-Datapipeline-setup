import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://postgres:galaxiq@66.135.22.167:5432/galaxiq_tenants"
TENANT_ID = "org_423b3ac30b46426db809c4196f7d358a"

async def main():
    engine = create_async_engine(DB_URL)
    async with engine.connect() as conn:
        # Check schema
        res = await conn.execute(
            text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema"),
            {"schema": TENANT_ID}
        )
        schema_exists = res.fetchone()
        
        if not schema_exists:
            print(f"Schema {TENANT_ID} DOES NOT exist.")
            return

        print(f"Schema {TENANT_ID} exists.")
        
        # Check tables
        res = await conn.execute(text(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{TENANT_ID}'
        """))
        tables = [row[0] for row in res.fetchall()]
        print(f"Tables in {TENANT_ID}: {tables}")

if __name__ == "__main__":
    asyncio.run(main())
