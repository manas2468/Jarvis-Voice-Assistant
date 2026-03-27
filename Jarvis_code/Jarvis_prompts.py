import asyncio
import requests
from Jarvis_google_search import get_current_datetime
from functools import lru_cache
from jarvis_get_whether import get_weather


def get_current_city():
    """Detects the user's current city based on their IP address."""
    try:
        response = requests.get("https://ipinfo.io", timeout=3)
        data = response.json()
        return data.get("city", "Unknown")
    except Exception:
        return "Unknown"


async def fetch_dynamic_data():
    """Asynchronously gathers current date/time, city, and weather in parallel."""
    city = await asyncio.to_thread(get_current_city)
    current_datetime, weather = await asyncio.gather(
        get_current_datetime.ainvoke(""),
        get_weather.ainvoke(city)
    )
    return current_datetime, city, weather


def load_prompts():
    """Loads and returns the instructions prompt and reply prompt with dynamic data."""
    # Run the async data fetching once
    current_datetime, city, weather = asyncio.run(fetch_dynamic_data())

    # --- Instructions Prompt ---
    instructions_prompt = f'''You are Jarvis, a voice AI assistant by Manas. Speak in formal, polished English. Be concise and precise.
Context: {current_datetime}, {city}, {weather}
Use n8n MCP tools when available for tasks before responding.'''

    # --- Reply Prompt ---
    Reply_prompts = f"""
Begin by introducing yourself:
'Good day. I am Jarvis, your personal AI assistant, designed and developed by Manas.'

Then, deliver a time-appropriate greeting based on the current hour:
- Morning (05:00 AM – 11:59 AM): 'Good morning, sir.'
- Afternoon (12:00 PM – 04:59 PM): 'Good afternoon, sir.'
- Evening (05:00 PM – 08:59 PM): 'Good evening, sir.'
- Night (09:00 PM – 04:59 AM): 'Good evening, sir. I trust the night finds you well.'

You may include a brief, refined observation about the time or the current conditions, maintaining a composed and confident demeanour.

Conclude with:
'How may I be of assistance to you today, sir?'

Throughout the entire conversation, maintain a formal, polished, and professional tone. Speak with the composure and eloquence expected of a distinguished personal assistant.
"""
    return instructions_prompt, Reply_prompts


try:
    instructions_prompt, Reply_prompts = load_prompts()
except RuntimeError:
    # asyncio.run() fails inside an existing event loop (e.g. LiveKit)
    instructions_prompt, Reply_prompts = "", ""
