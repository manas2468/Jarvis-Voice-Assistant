"""
Vision Engine for Jarvis — Multimodal Vision & Screen Awareness
================================================================
Provides on-demand screen capture and webcam analysis via Gemini Vision API.
No continuous recording — captures only when a tool is invoked.

Usage as LiveKit agent tool:
    from vision_engine import analyze_screen_tool, analyze_webcam_tool
    # Then register with agent (see bottom of file for integration example)

Usage standalone:
    result = await analyze_screen("Summarize what's on screen")
    result = await analyze_webcam("What am I holding?")
"""

import asyncio
import io
import os
import logging
import threading
from typing import Optional

import cv2
import numpy as np
import mss
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vision_engine")

# ──────────── BROWSER FRAME BUFFER ────────────────────
# Stores the latest webcam frame sent from the browser frontend.
# When available, this is used instead of local cv2.VideoCapture.
_browser_frame: Optional[np.ndarray] = None
_browser_frame_lock = threading.Lock()


def set_browser_frame(frame_bgr: np.ndarray):
    """Store a BGR numpy frame received from the browser's webcam."""
    global _browser_frame
    with _browser_frame_lock:
        _browser_frame = frame_bgr.copy()


def get_browser_frame() -> Optional[np.ndarray]:
    """Return the latest browser frame, or None if unavailable."""
    with _browser_frame_lock:
        return _browser_frame.copy() if _browser_frame is not None else None

# ─────────────────────── CONFIG ───────────────────────
VISION_MODEL = "gemini-2.0-flash"
MAX_IMAGE_SIZE = 1024       # max dimension in px before resize
JPEG_QUALITY = 75           # compression quality (1-100)

VISION_SYSTEM_PROMPT = (
    "You are Jarvis's visual cortex. Analyze the provided image based on "
    "the user's specific voice query. Be concise and prioritize technical "
    "accuracy (e.g., code errors, document headers, object names)."
)

# ─────────────────────── CLIENT ───────────────────────
_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set in environment")
        _client = genai.Client(api_key=api_key)
    return _client


# ─────────────────── IMAGE HELPERS ────────────────────
def _compress_image(img: Image.Image) -> bytes:
    """Resize + JPEG-compress an image for minimal API latency."""
    w, h = img.size
    if max(w, h) > MAX_IMAGE_SIZE:
        ratio = MAX_IMAGE_SIZE / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    data = buf.getvalue()
    logger.info(f"Image compressed: {w}x{h} → {img.size[0]}x{img.size[1]}, {len(data)//1024}KB")
    return data


# ─────────────────── CAPTURE FUNCTIONS ────────────────
def capture_screen() -> Image.Image:
    """Capture full primary monitor as PIL Image. Fast, no continuous recording."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # primary monitor
        shot = sct.grab(monitor)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def capture_webcam() -> Optional[Image.Image]:
    """Grab a single frame — from browser cam if available, else local webcam."""
    # 1) Try browser-provided frame first
    browser_frame = get_browser_frame()
    if browser_frame is not None:
        logger.info("Using browser webcam frame")
        return Image.fromarray(cv2.cvtColor(browser_frame, cv2.COLOR_BGR2RGB))

    # 2) Fallback to local webcam
    logger.info("No browser frame, falling back to local webcam")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Cannot open webcam")
        return None
    try:
        ret, frame = cap.read()
        if not ret:
            logger.error("Failed to read webcam frame")
            return None
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    finally:
        cap.release()


# ────────────────── VISION API CALL ───────────────────
async def _query_vision(image: Image.Image, query: str) -> str:
    """Send compressed image + query to Gemini Vision and return text response."""
    client = _get_client()
    img_bytes = await asyncio.to_thread(_compress_image, image)
    image_part = types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
    prompt = f"{VISION_SYSTEM_PROMPT}\n\nUser Query: {query}"

    try:
        resp = await client.aio.models.generate_content(
            model=VISION_MODEL,
            contents=[prompt, image_part],
        )
        return resp.text
    except Exception as e:
        logger.error(f"Vision API error: {e}")
        return f"Vision analysis failed: {e}"


# ══════════════════ PUBLIC ASYNC API ══════════════════
async def analyze_screen(query: str) -> str:
    """Capture screen + analyze with vision AI. Call on 'Summarize screen' etc."""
    logger.info(f"Screen analysis: {query}")
    try:
        screenshot = await asyncio.to_thread(capture_screen)
        return await _query_vision(screenshot, query)
    except Exception as e:
        logger.error(f"Screen analysis error: {e}")
        return f"Screen capture failed: {e}"


async def analyze_webcam(query: str) -> str:
    """Capture webcam frame + analyze with vision AI. Call on 'What am I looking at?' etc."""
    logger.info(f"Webcam analysis: {query}")
    try:
        frame = await asyncio.to_thread(capture_webcam)
        if frame is None:
            return "Could not access webcam. Check that a camera is connected."
        return await _query_vision(frame, query)
    except Exception as e:
        logger.error(f"Webcam analysis error: {e}")
        return f"Webcam capture failed: {e}"


# ══════════════ LIVEKIT AGENT TOOL WRAPPERS ═══════════
# These use livekit.agents.llm.function_tool decorator so they
# can be registered directly with a LiveKit Agent via agent._tools

def create_livekit_tools():
    """
    Returns a list of LiveKit-compatible tool functions for vision.
    Call once and extend agent._tools with the result.
    """
    from livekit.agents.llm import function_tool

    @function_tool()
    async def screen_analysis(query: str) -> str:
        """Captures a screenshot of the user's screen and analyzes it with vision AI.
        Use when the user says things like 'look at my screen', 'summarize this screen',
        'what's on my screen', 'debug this code', 'read this error message',
        or any request that requires seeing the screen content."""
        return await analyze_screen(query)

    @function_tool()
    async def webcam_analysis(query: str) -> str:
        """Captures a single frame from the user's webcam and analyzes it with vision AI.
        Use when the user says things like 'what am I looking at', 'identify this',
        'what am I holding', 'what do you see', 'look at this',
        or any request that requires seeing through the camera."""
        return await analyze_webcam(query)

    return [screen_analysis, webcam_analysis]


# ══════════════ LANGCHAIN TOOL WRAPPERS ═══════════════
# For use with LangChain-based flows or the local_jarvis.py server

from langchain.tools import tool as langchain_tool


@langchain_tool
async def analyze_screen_lc(query: str) -> str:
    """Captures a screenshot and analyzes it. Use when user asks about screen content,
    code debugging, error messages, or anything visible on screen."""
    return await analyze_screen(query)


@langchain_tool
async def analyze_webcam_lc(query: str) -> str:
    """Captures a webcam frame and analyzes it. Use when user asks about what
    they're looking at, holding, or showing to the camera."""
    return await analyze_webcam(query)


# ═══════════════════ QUICK TEST ═══════════════════════
if __name__ == "__main__":
    async def _test():
        print("Testing screen capture...")
        result = await analyze_screen("Describe what you see on this screen in 2 sentences.")
        print(f"Screen: {result}\n")

        print("Testing webcam capture...")
        result = await analyze_webcam("Describe what you see in 1 sentence.")
        print(f"Webcam: {result}")

    asyncio.run(_test())
