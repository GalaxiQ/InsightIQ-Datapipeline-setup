import asyncio
import logging
import sys

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

# Modify path so we can import 'app'
import sys
import os
sys.path.append(os.getcwd())

from app.core.llm import analyze_sentiment

async def test_llm():
    print("Testing Azure OpenAI connection...")
    text = "I absolutely love this new product! It's amazing and works perfectly."
    print(f"Input text: '{text}'")
    
    try:
        result = await analyze_sentiment(text)
        print("\n--- Result ---")
        print(result)
        
        if result.get("sentiment") == "positive":
            print("\nSUCCESS: Sentiment analysis returned expected positive result.")
        else:
            print(f"\nWARNING: Setup seems to work but result was: {result.get('sentiment')}")
            
    except Exception as e:
        print(f"\nERROR: Failed to connect or analyze: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm())
