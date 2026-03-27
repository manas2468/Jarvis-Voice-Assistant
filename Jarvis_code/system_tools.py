"""
System Tools — LiveKit function_tool wrappers for system control.
Bridges keyboard_mouse_CTRL and Jarvis_window_CTRL into LiveKit agent.
"""

from typing import List


def create_system_tools():
    """Returns a list of LiveKit-compatible system control tools."""
    from livekit.agents.llm import function_tool
    from keyboard_mouse_CTRL import controller, with_temporary_activation
    from Jarvis_window_CTRL import open_app as _open_app, close_app as _close_app, folder_file as _folder_file

    @function_tool()
    async def move_mouse(direction: str, distance: int = 100) -> str:
        """Moves the mouse cursor in a direction.
        Use when user says 'move mouse left', 'move cursor up', etc.
        direction must be one of: up, down, left, right."""
        return await with_temporary_activation(controller.move_cursor, direction, distance)

    @function_tool()
    async def click_mouse(button: str = "left") -> str:
        """Clicks the mouse button.
        Use when user says 'click', 'right click', 'double click'.
        button must be one of: left, right, double."""
        return await with_temporary_activation(controller.mouse_click, button)

    @function_tool()
    async def scroll(direction: str, amount: int = 10) -> str:
        """Scrolls the screen up or down.
        Use when user says 'scroll down', 'scroll up'.
        direction must be: up or down."""
        return await with_temporary_activation(controller.scroll_cursor, direction, amount)

    @function_tool()
    async def type_text(text: str) -> str:
        """Types text using the keyboard character by character.
        Use when user says 'type hello world', 'write the following'.
        text: the string to type."""
        return await with_temporary_activation(controller.type_text, text)

    @function_tool()
    async def press_key(key: str) -> str:
        """Presses a single keyboard key.
        Use when user says 'press enter', 'press escape', 'hit the space bar'.
        key: name of the key (e.g. enter, esc, tab, a, 1)."""
        return await with_temporary_activation(controller.press_key, key)

    @function_tool()
    async def press_hotkey(keys: str) -> str:
        """Presses a keyboard shortcut / hotkey combination.
        Use when user says 'save the file', 'undo', 'copy', 'paste', 'close window'.
        keys: comma-separated key names (e.g. 'ctrl,s' or 'alt,f4')."""
        key_list = [k.strip() for k in keys.split(",")]
        return await with_temporary_activation(controller.press_hotkey, key_list)

    @function_tool()
    async def volume_control(action: str) -> str:
        """Controls system volume.
        Use when user says 'increase volume', 'mute', 'lower the volume'.
        action must be one of: up, down, mute."""
        return await with_temporary_activation(controller.control_volume, action)

    @function_tool()
    async def open_application(app_name: str) -> str:
        """Opens a desktop application.
        Use when user says 'open chrome', 'launch notepad', 'start calculator'.
        app_name: name of the application."""
        return await _open_app.ainvoke(app_name)

    @function_tool()
    async def close_application(window_title: str) -> str:
        """Closes a desktop application by its window title.
        Use when user says 'close chrome', 'close notepad', 'exit vlc'.
        window_title: title of the window to close."""
        return await _close_app.ainvoke(window_title)

    @function_tool()
    async def manage_files(command: str) -> str:
        """Manages files and folders — open, create, rename, or delete.
        Use when user says 'open the music folder', 'create a folder called Projects',
        'rename OldName to NewName', 'delete xyz.mp4', 'play resume.pdf'.
        command: natural language file/folder command."""
        return await _folder_file.ainvoke(command)

    return [
        move_mouse, click_mouse, scroll, type_text,
        press_key, press_hotkey, volume_control,
        open_application, close_application, manage_files,
    ]
