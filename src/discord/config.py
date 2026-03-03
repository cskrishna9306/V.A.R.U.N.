# Import standard packages
import os
from dotenv import load_dotenv

# Import custom packages
from src.llm.utils import (
    get_weather,
)

# Load environment variables
load_dotenv()

# Get the discord bot token from the environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# The unique Guild ID for "The Bois" discord server
BOIS_GUILD_ID = 1294893602568409128

# Define tools for public use
PUBLIC_TOOLS = [get_weather]

# Define tools for admin use
ADMIN_TOOLS = PUBLIC_TOOLS + []

