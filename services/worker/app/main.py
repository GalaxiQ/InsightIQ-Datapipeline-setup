import asyncio
import logging
import sys
from app.worker import SentimentWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)

if __name__ == "__main__":
    worker = SentimentWorker()
    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        logging.info("Worker stopped by user")
