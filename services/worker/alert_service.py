import asyncpg
import asyncio

SQL = """
SELECT
  d.account_id,
  d.followers,
  lag(d.followers) OVER (ORDER BY last_updated) AS prev
FROM dim_account d
"""

async def run():
    conn = await asyncpg.connect("postgresql://...")
    while True:
        rows = await conn.fetch(SQL)
        for r in rows:
            if r["prev"] and abs(r["followers"] - r["prev"]) > 500:
                print("ALERT:", r["account_id"])
        await asyncio.sleep(60)

asyncio.run(run())
