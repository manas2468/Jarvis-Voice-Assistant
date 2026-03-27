import os
import subprocess
import logging
import sys
import asyncio
import time as _time
from fuzzywuzzy import process

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

from langchain.tools import tool

# Setup encoding and logger
sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Cached item index (avoids re-walking D:/ on every call) ──
_item_index_cache = []
_item_index_timestamp = 0
_ITEM_INDEX_TTL = 300  # seconds (5 minutes)


async def get_cached_index(folders):
    """Return cached item index, refreshing only if older than TTL."""
    global _item_index_cache, _item_index_timestamp
    if _time.time() - _item_index_timestamp > _ITEM_INDEX_TTL or not _item_index_cache:
        _item_index_cache = await index_items(folders)
        _item_index_timestamp = _time.time()
    return _item_index_cache


# Application command mapping (uses dynamic user path)
_USER_LOCAL = os.path.join(os.environ.get("LOCALAPPDATA", ""))
APP_MAPPINGS = {
    "notepad": "notepad",
    "calculator": "calc",
    "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "vlc": "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
    "command prompt": "cmd",
    "control panel": "control",
    "settings": "start ms-settings:",
    "paint": "mspaint",
    "vs code": os.path.join(_USER_LOCAL, "Programs", "Microsoft VS Code", "Code.exe"),
    "postman": os.path.join(_USER_LOCAL, "Postman", "Postman.exe"),
}

# -------------------------
# Global focus utility
# -------------------------
async def focus_window(title_keyword: str) -> bool:
    """Attempts to bring the specified window to the foreground."""
    if not gw:
        logger.warning("pygetwindow is not available. Window focus is not supported.")
        return False

    await asyncio.sleep(1.5)  # Allow time for the window to appear
    title_keyword = title_keyword.lower().strip()

    for window in gw.getAllWindows():
        if title_keyword in window.title.lower():
            if window.isMinimized:
                window.restore()
            window.activate()
            return True
    return False


# Index files and folders
async def index_items(base_dirs):
    """Indexes all files and folders within the specified directories."""
    item_index = []
    for base_dir in base_dirs:
        for root, dirs, files in os.walk(base_dir):
            for d in dirs:
                item_index.append({"name": d, "path": os.path.join(root, d), "type": "folder"})
            for f in files:
                item_index.append({"name": f, "path": os.path.join(root, f), "type": "file"})
    logger.info(f"Successfully indexed {len(item_index)} items.")
    return item_index


async def search_item(query, index, item_type):
    """Searches the index for an item matching the given query using fuzzy matching."""
    filtered = [item for item in index if item["type"] == item_type]
    choices = [item["name"] for item in filtered]
    if not choices:
        return None
    best_match, score = process.extractOne(query, choices)
    logger.info(f"Matched '{query}' to '{best_match}' with score {score}")
    if score > 70:
        for item in filtered:
            if item["name"] == best_match:
                return item
    return None


# File and folder actions
async def open_folder(path):
    """Opens the specified folder using the system's default file explorer."""
    try:
        os.startfile(path) if os.name == 'nt' else subprocess.call(['xdg-open', path])
        await focus_window(os.path.basename(path))
    except Exception as e:
        logger.error(f"Failed to open folder: {e}")


async def play_file(path):
    """Opens the specified file using the system's default application."""
    try:
        os.startfile(path) if os.name == 'nt' else subprocess.call(['xdg-open', path])
        await focus_window(os.path.basename(path))
    except Exception as e:
        logger.error(f"Failed to open file: {e}")


async def create_folder(path):
    """Creates a new folder at the specified path."""
    try:
        os.makedirs(path, exist_ok=True)
        return f"Folder created successfully: {path}"
    except Exception as e:
        return f"Failed to create folder: {e}"


async def rename_item(old_path, new_path):
    """Renames a file or folder from the old path to the new path."""
    try:
        os.rename(old_path, new_path)
        return f"Successfully renamed to: {new_path}"
    except Exception as e:
        return f"Failed to rename the item: {e}"


async def delete_item(path):
    """Deletes the file or folder at the specified path."""
    try:
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)
        return f"Successfully deleted: {path}"
    except Exception as e:
        return f"Failed to delete the item: {e}"


# Application control tools
@tool
async def open_app(app_title: str) -> str:
    """
    Launches a desktop application such as Notepad, Chrome, VLC, etc.

    Use this tool when the user requests to open or launch an application
    on their computer.

    Example prompts:
    - "Open Notepad"
    - "Launch Chrome"
    - "Start VLC media player"
    - "Open the Calculator"
    """

    app_title = app_title.lower().strip()
    app_command = APP_MAPPINGS.get(app_title, app_title)
    try:
        await asyncio.create_subprocess_shell(f'start "" "{app_command}"', shell=True)
        focused = await focus_window(app_title)
        if focused:
            return f"Application launched and focused successfully: {app_title}."
        else:
            return f"Application launched successfully: {app_title}. However, the window could not be brought into focus."
    except Exception as e:
        return f"Failed to launch application '{app_title}': {e}"


@tool
async def close_app(window_title: str) -> str:
    """
    Closes an application window by its title.

    Use this tool when the user wishes to close any application or window
    on their desktop.

    Example prompts:
    - "Close Notepad"
    - "Close VLC"
    - "Close the Chrome window"
    - "Close the Calculator"
    """

    if not win32gui:
        return "The win32gui module is not available. Unable to close the window."

    def enumHandler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            if window_title.lower() in win32gui.GetWindowText(hwnd).lower():
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)

    win32gui.EnumWindows(enumHandler, None)
    return f"The window has been closed: {window_title}"


# Folder and file management tool
@tool
async def folder_file(command: str) -> str:
    """
    Handles folder and file actions such as open, create, rename, or delete
    based on a natural language command.

    Use this tool when the user wishes to manage folders or files using
    natural language instructions.

    Example prompts:
    - "Create a folder called Projects"
    - "Rename OldName to NewName"
    - "Delete xyz.mp4"
    - "Open the Music folder"
    - "Play Resume.pdf"
    """

    folders_to_index = ["D:/"]
    index = await get_cached_index(folders_to_index)
    command_lower = command.lower()

    if "create folder" in command_lower:
        folder_name = command.replace("create folder", "").strip()
        path = os.path.join("D:/", folder_name)
        return await create_folder(path)

    if "rename" in command_lower:
        parts = command_lower.replace("rename", "").strip().split("to")
        if len(parts) == 2:
            old_name = parts[0].strip()
            new_name = parts[1].strip()
            item = await search_item(old_name, index, "folder")
            if item:
                new_path = os.path.join(os.path.dirname(item["path"]), new_name)
                return await rename_item(item["path"], new_path)
        return "The rename command is not valid. Please use the format: rename [old name] to [new name]."

    if "delete" in command_lower:
        item = await search_item(command, index, "folder") or await search_item(command, index, "file")
        if item:
            return await delete_item(item["path"])
        return "The item to delete could not be found."

    if "folder" in command_lower or "open folder" in command_lower:
        item = await search_item(command, index, "folder")
        if item:
            await open_folder(item["path"])
            return f"Folder opened successfully: {item['name']}"
        return "The requested folder could not be found."

    item = await search_item(command, index, "file")
    if item:
        await play_file(item["path"])
        return f"File opened successfully: {item['name']}"

    return "No matching file or folder was found for the given command."
