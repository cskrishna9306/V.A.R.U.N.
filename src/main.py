# Import standard packages
import asyncio

# Import third-party packages
import uvicorn

# Import custom packages
from src.discord.bot import DiscordBot
from src.discord.config import DISCORD_BOT_TOKEN
from src.app import app as fastapi_app

async def main():
    """
    Main coroutine that runs the Discord bot and the FastAPI health server concurrently.
    """
    bot = DiscordBot()

    server = uvicorn.Server(uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="info"))

    async with bot:
        # Run the bot and the health server side by side; if either exits, so does the process
        await asyncio.gather(
            bot.start(DISCORD_BOT_TOKEN),
            server.serve(),
        )

    return

if __name__ == "__main__":
    asyncio.run(main())
