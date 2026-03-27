import asyncio
from datetime import datetime
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext, ChatMessage
from livekit.plugins import google, noise_cancellation

# Import custom modules
from memory_loop import MemoryExtractor
from mcp_client.server import MCPServerSse
from mcp_client.agent_tools import MCPToolsIntegration
from vision_engine import create_livekit_tools as create_vision_tools
from system_tools import create_system_tools
import os
from mem0 import AsyncMemoryClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

mem0_client = AsyncMemoryClient()
user_id = "Manas_48"


def get_fresh_prompts():
    """Generate prompts with CURRENT time — safe to call from async context."""
    now = datetime.now()
    hour = now.hour
    day_name = now.strftime("%A")
    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%d %B %Y")

    if 5 <= hour < 12:
        greet = "Good morning, sir."
        period = "morning"
    elif 12 <= hour < 17:
        greet = "Good afternoon, sir."
        period = "afternoon"
    elif 17 <= hour < 21:
        greet = "Good evening, sir."
        period = "evening"
    else:
        greet = "Good evening, sir. I trust the night finds you well."
        period = "night"

    instructions = (
        f"You are Jarvis — an advanced voice-based AI assistant, designed by Manas. "
        f"Communicate in formal, polished English. Be concise and precise. "
        f"IMPORTANT — The current time RIGHT NOW is: {time_str} IST, "
        f"{day_name}, {date_str}. It is currently {period} ({hour}:00 hour). "
        f"ALWAYS use this exact time when asked. NEVER guess a different time. "
        f"Use available tools when a task can be accomplished through them. "
        f"You have detection capabilities: use detection_mode to start/stop real-time "
        f"object detection on the webcam. Use what_do_you_see to report what objects "
        f"are currently visible. Use screen_analysis for screen content analysis. "
        f"Use webcam_analysis for single-frame camera analysis. "
        f"IMPORTANT — KEEP RESPONSES EXTREMELY BRIEF (under 15 words) unless asked for more."
    )
    reply = (
        f"Say: '{greet} I am Jarvis. How may I assist you today, sir?'"
    )
    return instructions, reply


class Assistant(Agent):
    def __init__(self, chat_ctx) -> None:
        instructions, _ = get_fresh_prompts()
        super().__init__(
            instructions=instructions,
            chat_ctx=chat_ctx,
            llm=google.beta.realtime.RealtimeModel(
                model="gemini-2.5-flash-native-audio-preview-12-2025",
                voice="Charon"
            )
        )
        # Register all tools: vision + detection + system control
        try:
            all_tools = (
                create_vision_tools()
                + create_system_tools()
            )
            if hasattr(self, '_tools') and isinstance(self._tools, list):
                self._tools.extend(all_tools)
            else:
                self._tools = list(all_tools)
            logger.info(f"Tools registered: {[t.__name__ for t in all_tools]}")
        except Exception as e:
            logger.warning(f"Tools not loaded: {e}")


async def _fetch_memories_background(session, user_id):
    """Fetch memories in background and inject into session context without blocking."""
    try:
        all_memories = await mem0_client.get_all(user_id=user_id)
        memory_str = "\n".join([m.get('memory', '') or m.get('text', '') for m in all_memories])
        if memory_str:
            logger.info(f"Loaded {len(all_memories)} memories for user: {user_id}")
            # Inject memories into the live session as context
            memory_context = (
                f"Here are things you remember about the user from past conversations:\n"
                f"{memory_str}\n"
                f"Use these memories to personalize your responses."
            )
            await session.generate_reply(instructions=memory_context)
    except Exception as e:
        logger.error(f"Error fetching memories in background: {e}")


async def entrypoint(ctx: agents.JobContext):
    logger.info(f"Starting agent for user: {user_id}")

    # Configure the session immediately — don't wait for memories
    session = AgentSession(
        preemptive_generation=True
    )
    current_ctx = session.history.items

    # Lightweight initial context (no blocking API call)
    initial_ctx = ChatContext()
    initial_ctx.add_message(
        role="assistant",
        content=f"The user's name is {user_id}."
    )

    agent_instance = Assistant(chat_ctx=initial_ctx)

    # Start the agent immediately
    await session.start(
        room=ctx.room,
        agent=agent_instance,
        room_input_options=RoomInputOptions(),
    )
    await asyncio.sleep(1)
    
    instructions, reply_prompt = get_fresh_prompts()
    try:
        await session.generate_reply(
            instructions=reply_prompt
        )
        logger.info(f"Greeting requested: {reply_prompt}")
    except Exception as e:
        logger.error(f"Failed to generate greeting: {e}")

    # Fire-and-forget: fetch memories in background
    asyncio.create_task(_fetch_memories_background(session, user_id))

    # Connect MCP server and register tools in background (non-blocking)

    # Connect MCP server and register tools in background (non-blocking)
    asyncio.create_task(_connect_mcp_tools(agent_instance))

    conv_ctx = MemoryExtractor()
    await conv_ctx.run(current_ctx)


async def _connect_mcp_tools(agent_instance):
    """Connect to the n8n MCP server and register its tools with the agent."""
    mcp_url = os.getenv("N8N_MCP_SERVER_URL")
    if not mcp_url:
        logger.info("N8N_MCP_SERVER_URL not set, skipping MCP tools")
        return
    try:
        mcp_server = MCPServerSse(
            params={"url": mcp_url, "timeout": 10},
            cache_tools_list=True,
            name="n8n MCP Server"
        )
        tools = await MCPToolsIntegration.register_with_agent(
            agent_instance, [mcp_server], auto_connect=True
        )
        logger.info(f"MCP tools registered: {len(tools)}")
    except Exception as e:
        logger.warning(f"MCP connection failed (non-fatal): {e}")





if __name__ == "__main__":
    import sys
    import asyncio

    # --- Windows Specific Fix ---
    if sys.platform == "win32":
        # Force the use of ProactorEventLoop on Windows
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        # Create a loop manually to avoid the "no current event loop" error
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    # ----------------------------

    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))