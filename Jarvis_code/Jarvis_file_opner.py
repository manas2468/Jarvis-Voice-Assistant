import os
import subprocess
import sys
import logging
from fuzzywuzzy import process
import asyncio
try:
    import pygetwindow as gw
except ImportError:
    gw = None

from langchain.tools import tool
import time as _time

sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Cached file index (avoids re-walking D:/ on every call) ──
_file_index_cache = []
_file_index_timestamp = 0
_FILE_INDEX_TTL = 300  # seconds (5 minutes)


async def get_cached_index(folders):
    """Return cached file index, refreshing only if older than TTL."""
    global _file_index_cache, _file_index_timestamp
    if _time.time() - _file_index_timestamp > _FILE_INDEX_TTL or not _file_index_cache:
        _file_index_cache = await index_files(folders)
        _file_index_timestamp = _time.time()
    return _file_index_cache


async def focus_window(title_keyword: str) -> bool:
    """Attempts to bring the specified window to the foreground."""
    if not gw:
        logger.warning("pygetwindow is not available. Window focus is not supported.")
        return False

    await asyncio.sleep(1.5)
    title_keyword = title_keyword.lower().strip()

    for window in gw.getAllWindows():
        if title_keyword in window.title.lower():
            if window.isMinimized:
                window.restore()
            window.activate()
            logger.info(f"Window is now in focus: {window.title}")
            return True
    logger.warning("No matching window was found to bring into focus.")
    return False


async def index_files(base_dirs):
    """Indexes all files within the specified directories."""
    file_index = []
    for base_dir in base_dirs:
        for root, _, files in os.walk(base_dir):
            for f in files:
                file_index.append({
                    "name": f,
                    "path": os.path.join(root, f),
                    "type": "file"
                })
    logger.info(f"Successfully indexed {len(file_index)} files from {base_dirs}.")
    return file_index


async def search_file(query, index):
    """Searches the index for a file matching the given query using fuzzy matching."""
    choices = [item["name"] for item in index]
    if not choices:
        logger.warning("No files are available to match against.")
        return None

    best_match, score = process.extractOne(query, choices)
    logger.info(f"Matched '{query}' to '{best_match}' (Score: {score})")
    if score > 70:
        for item in index:
            if item["name"] == best_match:
                return item
    return None


async def open_file(item):
    """Opens the specified file using the system's default application."""
    try:
        logger.info(f"Opening file: {item['path']}")
        if os.name == 'nt':
            os.startfile(item["path"])
        else:
            subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', item["path"]])
        await focus_window(item["name"])
        return f"File opened successfully: {item['name']}"
    except Exception as e:
        logger.error(f"Failed to open file: {e}")
        return f"An error occurred while opening the file: {e}"


async def handle_command(command, index):
    """Handles the user's file command by searching and opening the file."""
    item = await search_file(command, index)
    if item:
        return await open_file(item)
    else:
        logger.warning("The requested file could not be found.")
        return "The requested file could not be found."


@tool
async def Play_file(name: str) -> str:
    """
    Searches for and opens a file by name from the D:/ drive.

    Use this tool when the user wishes to open a file such as a video,
    PDF, document, image, or any other file type.

    Example prompts:
    - "Open my resume from D drive"
    - "Open D:/project report"
    - "Play the MP4 file"
    """

    folders_to_index = ["D:/"]
    index = await get_cached_index(folders_to_index)
    command = name.strip()
    return await handle_command(command, index)
