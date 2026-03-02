# Import custom packages
from src.discord.bot import DiscordBot
from src.discord.config import DISCORD_BOT_TOKEN

def main():
    """
    Main function to run the Discord bot.
    """
    bot = DiscordBot()
    
    # Launch the bot
    bot.run(DISCORD_BOT_TOKEN)
    
    return

if __name__ == "__main__":
    main()