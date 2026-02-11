import asyncio
import argparse
import random
import uuid
import json
import logging
from datetime import datetime, timedelta
import sys
import os

# Ensure we can import 'app'
# script is in services/api/scripts/
# we want to add services/api/ to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.core.db import get_db, SessionLocal, engine as master_engine
from app.core.tenant_store import get_tenant_db
from app.core.tenant_db import get_tenant_session
from app.core.tenant_schema import tenant_schema_name

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock-data-generator")

PLATFORMS = ["instagram", "twitter", "linkedin"]
BRANDS = ["InsightIQ_Demo"]

# Helper to generate random timestamps
def random_date(start_date, end_date):
    delta = end_date - start_date
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start_date + timedelta(seconds=random_second)

def generate_text():
    words = ["amazing", "innovation", "AI", "cloud", "data", "future", "tech", "growth", "strategy", "insights", 
             "platform", "scalable", "secure", "community", "connect", "global", "impact", "transform", "digital"]
    return " ".join(random.sample(words, k=random.randint(5, 15)))

class DataGenerator:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.posts = []
        self.interactions = []
        self.metrics = []
        self.accounts = []

    def generate_posts(self, count=200):
        print(f"Generating {count} posts...")
        start_date = datetime.now() - timedelta(days=90)
        end_date = datetime.now()

        for _ in range(count):
            platform = random.choice(PLATFORMS)
            brand = random.choice(BRANDS)
            created_at = random_date(start_date, end_date)
            post_id = str(uuid.uuid4())
            
            payload = {}
            if platform == "instagram":
                payload = {
                    "post_id": post_id,
                    "caption": generate_text(),
                    "media_type": random.choice(["IMAGE", "VIDEO", "CAROUSEL_ALBUM"]),
                    "media_url": f"https://s3.amazonaws.com/mock-images/{uuid.uuid4()}.jpg",
                    "permalink": f"https://instagram.com/p/{uuid.uuid4()}/",
                    "created_at": created_at.isoformat(),
                    "metrics": {
                        "likes": random.randint(10, 5000),
                        "comments": random.randint(0, 500)
                    },
                    "owner": {"id": "17841400000000001"}
                }
            elif platform == "twitter":
                payload = {
                    "post_id": post_id,
                    "text": generate_text(),
                    "created_at": created_at.isoformat(),
                    "author_id": "2244994945",
                    "lang": "en",
                    "metrics": {
                        "retweet_count": random.randint(0, 1000),
                        "reply_count": random.randint(0, 200),
                        "likes": random.randint(0, 2000),
                        "quote_count": random.randint(0, 50)
                    }
                }
            elif platform == "linkedin":
                payload = {
                    "post_id": post_id, 
                    "author": "urn:li:organization:1234567",
                    "created_at": created_at.isoformat(),
                    "metrics": {
                        "likes": random.randint(0, 500),
                        "comments": random.randint(0, 100),
                        "shares": random.randint(0, 50)
                    },
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {"text": generate_text()}
                        }
                    }
                }

            self.posts.append({
                "platform": platform,
                "brand": brand,
                "fetched_at": datetime.now(),
                "raw_json": json.dumps(payload),
                "post_id": post_id, # store for generating interactions
                "created_at": created_at
            })

    def generate_interactions(self, count_per_post=5):
        print(f"Generating interactions ({len(self.posts)} posts x ~{count_per_post} avg)...")
        for post in self.posts:
            # Generate random number of interactions for this post
            num_interactions = random.randint(0, count_per_post * 2)
            
            for _ in range(num_interactions):
                interaction_id = str(uuid.uuid4())
                created_at = post["created_at"] + timedelta(minutes=random.randint(1, 1440))
                
                payload = {}
                if post["platform"] == "instagram":
                    payload = {
                        "interaction_id": interaction_id,
                        "post_id": post["post_id"],
                        "text": generate_text(),
                        "created_at": created_at.isoformat(),
                        "user_id": str(uuid.uuid4())
                    }
                elif post["platform"] == "twitter":
                    payload = {
                        "interaction_id": interaction_id,
                        "post_id": post["post_id"],
                        "text": generate_text(),
                        "created_at": created_at.isoformat(),
                        "author_id": str(random.randint(100000, 999999))
                    }
                elif post["platform"] == "linkedin":
                    payload = {
                        "interaction_id": interaction_id,
                        "post_id": post["post_id"],
                        "message": generate_text(),
                        "created_at": created_at.isoformat(),
                        "actor": "urn:li:person:" + str(uuid.uuid4())
                    }

                self.interactions.append({
                    "platform": post["platform"],
                    "fetched_at": datetime.now(),
                    "raw_json": json.dumps(payload)
                })

    def generate_accounts(self):
        print("Generating account metadata for raw_events...")
        for brand in BRANDS:
            for platform in PLATFORMS:
                account_id = f"acc_{platform}_{brand}"
                payload = {
                    "id": account_id,
                    "name": f"{brand} {platform.capitalize()} Account",
                    "username": f"{brand.lower()}_{platform}",
                    "category": "Brand",
                    "followers_count": random.randint(1000, 100000),
                    "website": f"https://{brand.lower()}.com",
                    "overall_star_rating": round(random.uniform(4.0, 5.0), 1)
                }
                self.accounts.append({
                    "brand_id": brand,
                    "domain": "social",
                    "platform": platform,
                    "raw_json": json.dumps(payload),
                    "schema_version": "v1",
                    "payload_hash": str(uuid.uuid4())
                })

    def generate_account_metrics(self):
        print("Generating daily account metrics...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        current_date = start_date
        while current_date <= end_date:
            for platform in PLATFORMS:
                for brand in BRANDS:
                    # Simulate growth
                    days_passed = (current_date - start_date).days
                    base_followers = 1000
                    growth = days_passed * random.randint(5, 20)
                    
                    payload = {
                        "date": current_date.strftime("%Y-%m-%d"),
                        "follower_count": base_followers + growth,
                        "following_count": 50 + (days_passed // 10),
                        "total_posts": 100 + (days_passed // 3),
                        "impressions": random.randint(1000, 5000),
                        "reach": random.randint(800, 4000),
                        "profile_views": random.randint(50, 200)
                    }
                    
                    self.metrics.append({
                        "platform": platform,
                        "brand": brand,
                        "fetched_at": current_date, # Simulate historical fetch
                        "raw_json": json.dumps(payload)
                    })
            current_date += timedelta(days=1)

    async def seed(self):
        print(f"Connecting to Tenant DB for {self.tenant_id}...")
        
        # 1. Get Tenant Config
        async with SessionLocal() as master_session:
            try:
                tenant_cfg = await get_tenant_db(master_session, self.tenant_id)
            except Exception as e:
                print(f"Error fetching tenant config: {e}")
                return

        schema = tenant_schema_name(self.tenant_id)
        print(f"Target Schema: {schema}")

        # 2. Insert Data
        async for session in get_tenant_session(tenant_cfg):
            try:
                # Set schema path
                await session.execute(text(f'SET search_path TO "{schema}"'))

                # Insert Posts
                print(f"Inserting {len(self.posts)} posts...")
                for p in self.posts:
                    await session.execute(
                        text("""
                        INSERT INTO raw_social_posts (platform, brand, fetched_at, raw_json)
                        VALUES (:platform, :brand, :fetched_at, CAST(:raw_json AS jsonb))
                        """),
                        p
                    )
                
                # Insert Interactions
                print(f"Inserting {len(self.interactions)} interactions...")
                for interaction in self.interactions:
                    await session.execute(
                        text("""
                        INSERT INTO raw_social_interactions (platform, fetched_at, raw_json)
                        VALUES (:platform, :fetched_at, CAST(:raw_json AS jsonb))
                        """),
                        interaction
                    )
                
                # Insert Metrics
                print(f"Inserting {len(self.metrics)} account metrics...")
                for m in self.metrics:
                    await session.execute(
                        text("""
                        INSERT INTO raw_account_metrics (platform, brand, fetched_at, raw_json)
                        VALUES (:platform, :brand, :fetched_at, CAST(:raw_json AS jsonb))
                        """),
                        m
                    )

                # Insert Accounts (into raw_events)
                print(f"Inserting {len(self.accounts)} account metadata records...")
                for acc in self.accounts:
                    await session.execute(
                        text("""
                        INSERT INTO raw_events (brand_id, domain, platform, raw_json, schema_version, payload_hash)
                        VALUES (:brand_id, :domain, :platform, CAST(:raw_json AS jsonb), :schema_version, :payload_hash)
                        """),
                        acc
                    )

                await session.commit()
                print("✅ Data seeding complete!")
                
            except Exception as e:
                print(f"❌ Error seeding data: {e}")
                await session.rollback()

async def main():
    parser = argparse.ArgumentParser(description="Generate mock social media data")
    parser.add_argument("--tenant-id", type=str, required=True, help="Tenant ID to seed data into")
    args = parser.parse_args()

    generator = DataGenerator(args.tenant_id)
    generator.generate_posts(count=300) 
    generator.generate_interactions(count_per_post=8) 
    generator.generate_accounts()
    generator.generate_account_metrics()
    
    await generator.seed()

if __name__ == "__main__":
    asyncio.run(main())
