from mem0 import AsyncMemoryClient
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def clear_gaurav_memory():
    # It uses the API key from your .env automatically
    client = AsyncMemoryClient()
    # This deletes everything associated with the old ID
    await client.delete_all(user_id="Manas_48")
    print("Successfully deleted all memories for Manas_48")

if __name__ == "__main__":
    asyncio.run(clear_gaurav_memory())