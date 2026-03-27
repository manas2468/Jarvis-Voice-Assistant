import os
import asyncio
import requests
import logging
from dotenv import load_dotenv
from datetime import datetime
from langchain.tools import tool

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@tool
async def google_search(query: str) -> str:
    """
    Searches Google and returns the top 3 results with heading and summary only.
    No raw links are included to ensure the speech output sounds natural.

    Use this tool when the user requests a web search or asks a question that
    requires looking up current information online.

    Example prompts:
    - "Search for the latest news on artificial intelligence"
    - "Look up the population of Tokyo"
    - "Find information about climate change"
    """

    logger.info(f"Search query received: {query}")

    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    search_engine_id = os.getenv("SEARCH_ENGINE_ID")

    if not api_key or not search_engine_id:
        missing = []
        if not api_key:
            missing.append("GOOGLE_SEARCH_API_KEY")
        if not search_engine_id:
            missing.append("SEARCH_ENGINE_ID")
        return f"Missing environment variables: {', '.join(missing)}"

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": query,
        "num": 3
    }

    try:
        logger.info("Sending request to Google Custom Search API...")
        response = await asyncio.to_thread(requests.get, url, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return f"Google Search API request failed: {e}"

    if response.status_code != 200:
        logger.error(f"Google API error: {response.status_code} - {response.text}")
        return f"Google Search API returned an error: {response.status_code} - {response.text}"

    data = response.json()
    results = data.get("items", [])

    if not results:
        logger.info("No results were found for the given query.")
        return "No results were found for the given query."

    # Create a natural, speech-friendly summary
    formatted = "Here are the top results:\n"
    for i, item in enumerate(results, start=1):
        title = item.get("title", "No title")
        snippet = item.get("snippet", "").strip()
        formatted += f"{i}. {title}. {snippet}\n\n"

    return formatted.strip()


@tool
async def get_current_datetime() -> str:
    """
    Returns the current date and time in a human-readable format.

    Use this tool when the user asks for the current time, date,
    or wishes to know what day it is.

    Example prompts:
    - "What is the current time?"
    - "What is today's date?"
    - "Tell me the date and time right now."
    """

    now = datetime.now()
    formatted = now.strftime("%d %B %Y, %I:%M %p")  # Example: 31 July 2025, 04:22 PM
    return formatted