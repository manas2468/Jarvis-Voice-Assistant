"""Jarvis Local — Voice AI on localhost via Gemini Live API."""
import asyncio, base64, json, os, logging, traceback
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types

import cv2
import numpy as np

from jarvis_get_whether import get_weather
from Jarvis_google_search import google_search, get_current_datetime
from vision_engine import (
    set_browser_frame, analyze_screen, analyze_webcam
)
from detection_mode import (
    feed_frame, start_detection, stop_detection, get_detection_summary
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"

TOOLS = types.Tool(function_declarations=[
    types.FunctionDeclaration(name="get_weather",
        description="Get current weather for a city.",
        parameters=types.Schema(type=types.Type.OBJECT,
            properties={"city": types.Schema(type=types.Type.STRING, description="City name")}, required=["city"])),
    types.FunctionDeclaration(name="google_search",
        description="Search Google for current information.",
        parameters=types.Schema(type=types.Type.OBJECT,
            properties={"query": types.Schema(type=types.Type.STRING, description="Search query")}, required=["query"])),
    types.FunctionDeclaration(name="get_current_datetime",
        description="Get current date and time.",
        parameters=types.Schema(type=types.Type.OBJECT, properties={})),
    types.FunctionDeclaration(name="screen_analysis",
        description="Captures a screenshot of the user's screen and analyzes it with vision AI. Use when the user says 'look at my screen', 'what's on my screen', 'debug this code', etc.",
        parameters=types.Schema(type=types.Type.OBJECT,
            properties={"query": types.Schema(type=types.Type.STRING, description="What to analyze on the screen")}, required=["query"])),
    types.FunctionDeclaration(name="webcam_analysis",
        description="Analyzes the user's webcam feed with vision AI. Use when the user says 'what do you see', 'what am I showing', 'look at this', 'identify this', etc.",
        parameters=types.Schema(type=types.Type.OBJECT,
            properties={"query": types.Schema(type=types.Type.STRING, description="What to look for in the camera")}, required=["query"])),
    types.FunctionDeclaration(name="detection_mode",
        description="Activates or stops real-time object detection using the webcam. Use when user says 'detection mode', 'start detection', 'scan surroundings'.",
        parameters=types.Schema(type=types.Type.OBJECT,
            properties={"action": types.Schema(type=types.Type.STRING, description="'start' or 'stop'")}, required=["action"])),
    types.FunctionDeclaration(name="what_do_you_see",
        description="Reports what objects are currently detected in the camera feed.",
        parameters=types.Schema(type=types.Type.OBJECT, properties={})),
])


async def run_tool(name, args):
    try:
        if name == "get_weather": return await get_weather.ainvoke(args.get("city", ""))
        if name == "google_search": return await google_search.ainvoke(args.get("query", ""))
        if name == "get_current_datetime": return await get_current_datetime.ainvoke("")
        if name == "screen_analysis": return await analyze_screen(args.get("query", "Describe the screen"))
        if name == "webcam_analysis": return await analyze_webcam(args.get("query", "Describe what you see"))
        if name == "detection_mode":
            action = args.get("action", "start").lower()
            if action in ("stop", "off", "end", "deactivate"):
                return stop_detection()
            return start_detection()
        if name == "what_do_you_see":
            return get_detection_summary()
        return f"Unknown tool: {name}"
    except Exception as e:
        return f"Error: {e}"


def get_prompts():
    now = datetime.now()
    time_str = now.strftime("%d %B %Y, %I:%M %p")
    hour = now.hour
    if 5 <= hour < 12: greet = "Good morning, sir."
    elif 12 <= hour < 17: greet = "Good afternoon, sir."
    elif 17 <= hour < 21: greet = "Good evening, sir."
    else: greet = "Good evening, sir. I trust the night finds you well."
    instructions = (f"You are Jarvis, a formal voice AI assistant created by Manas. "
                    f"Be concise, precise, and polished. Current time: {time_str}. "
                    f"Use available tools when a task can be accomplished through them. "
                    f"You have vision capabilities: use webcam_analysis to see through the user's camera, "
                    f"screen_analysis for screen content, detection_mode for live object detection, "
                    f"and what_do_you_see to report detected objects. "
                    f"Keep responses short and conversational for voice.")
    reply = (f"Say exactly: '{greet} I am Jarvis, your personal AI assistant. "
             f"How may I be of assistance today, sir?' Keep it short and formal.")
    return instructions, reply


STATIC = os.path.join(os.path.dirname(__file__), "static")

@app.get("/")
async def index():
    return FileResponse(os.path.join(STATIC, "index.html"))

@app.get("/assistant")
async def assistant():
    return FileResponse(os.path.join(STATIC, "assistant.html"))


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    logger.info("Client connected")
    instructions, reply_prompt = get_prompts()
    client = genai.Client(api_key=GOOGLE_API_KEY)
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon"))),
        system_instruction=instructions,
        tools=[TOOLS],
    )
    try:
        async with client.aio.live.connect(model=MODEL, config=config) as session:
            logger.info("Gemini Live connected")
            await ws.send_text(json.dumps({"type": "status", "data": "connected"}))
            # Request greeting
            await session.send_client_content(
                turns=types.Content(role="user", parts=[types.Part(text=reply_prompt)]),
                turn_complete=True)

            async def from_browser():
                try:
                    while True:
                        raw = await ws.receive_text()
                        msg = json.loads(raw)
                        if msg["type"] == "audio":
                            await session.send_realtime_input(
                                audio=types.Blob(data=base64.b64decode(msg["data"]),
                                                 mime_type="audio/pcm;rate=16000"))
                        elif msg["type"] == "text":
                            await session.send_client_content(
                                turns=types.Content(role="user", parts=[types.Part(text=msg["data"])]),
                                turn_complete=True)
                        elif msg["type"] == "video":
                            # Decode JPEG frame from browser webcam
                            try:
                                jpg_bytes = base64.b64decode(msg["data"])
                                arr = np.frombuffer(jpg_bytes, dtype=np.uint8)
                                frame_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                                if frame_bgr is not None:
                                    set_browser_frame(frame_bgr)
                                    feed_frame(frame_bgr)
                            except Exception as e:
                                pass  # Skip bad frames silently
                except WebSocketDisconnect:
                    pass
                except Exception as e:
                    logger.error(f"from_browser error: {e}")

            async def to_browser():
                try:
                    async for resp in session.receive():
                        sc = resp.server_content
                        if sc:
                            if sc.model_turn:
                                for part in sc.model_turn.parts:
                                    if part.inline_data:
                                        await ws.send_text(json.dumps({
                                            "type": "audio",
                                            "data": base64.b64encode(part.inline_data.data).decode()}))
                                    if part.text:
                                        # Filter out thinking markers
                                        txt = part.text.strip()
                                        if txt and not txt.startswith("**"):
                                            await ws.send_text(json.dumps({"type": "text", "data": txt}))
                            if sc.turn_complete:
                                await ws.send_text(json.dumps({"type": "turn_complete"}))
                            if sc.interrupted:
                                await ws.send_text(json.dumps({"type": "interrupted"}))
                        if resp.tool_call:
                            resps = []
                            for fc in resp.tool_call.function_calls:
                                logger.info(f"Tool: {fc.name}({fc.args})")
                                await ws.send_text(json.dumps({"type": "tool", "data": fc.name}))
                                result = await run_tool(fc.name, fc.args or {})
                                resps.append(types.FunctionResponse(
                                    name=fc.name, response={"result": str(result)}, id=fc.id))
                            await session.send_tool_response(function_responses=resps)
                except WebSocketDisconnect:
                    pass
                except Exception as e:
                    logger.error(f"to_browser error: {e}")
                    traceback.print_exc()

            await asyncio.gather(from_browser(), to_browser())
    except Exception as e:
        logger.error(f"Session error: {e}")
        traceback.print_exc()
        try:
            await ws.send_text(json.dumps({"type": "error", "data": str(e)}))
        except: pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
