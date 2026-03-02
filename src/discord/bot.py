# Import Discord packages
import discord
from discord.ext import commands
from discord import app_commands

# Import custom packages
from src.llm.orchestrator import V_A_R_U_N
from src.discord.config import (
    ADMIN_TOOLS,
    BOIS_GUILD_ID,
    PUBLIC_TOOLS,
)
# from src.discord.cogs.tools import get_weather

class DiscordBot(commands.Bot):
    """
    The Discord Bot that utilizes the V.A.R.U.N. agent for fun and interactive conversations within a discord server.
    """
    
    def __init__(self):
        # Setup intents
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        
        # Initialize the public V.A.R.U.N. agent
        self.public_agent = V_A_R_U_N(tools=PUBLIC_TOOLS)
        
        # Initialize the admin V.A.R.U.N. agent
        self.admin_agent = V_A_R_U_N(tools=ADMIN_TOOLS)
        
        return

    async def setup_hook(self):
        """
        Method is responsible for pushing instant updates to certain servers while registering all slash commands with the bot.
        """
        
        # Load the cogs
        await self.load_extension("src.discord.cogs.yap")
        
        MY_GUILD = discord.Object(id=BOIS_GUILD_ID)
        self.tree.copy_global_to(guild=MY_GUILD)
        
        # Sync the slash commands
        await self.tree.sync(guild=MY_GUILD)
        print("Slash commands synced!")
        
        return

    async def on_ready(self):
        """
        Simple coroutine that prints out the logged in user to the console.
        """
        print(f"Logged in as {self.user}")
        return

    # @bot.event
    async def on_message(self, message: discord.Message):
        """
        Method that gets triggered upon any and every message in the channel this bot is added to.

        Args:
            message (discord.Message): The message object that triggered this event.
        """
        # Ignore the bot itself
        if message.author.bot:
            return
        
        # Simple reply to "Hello"s
        if message.content.lower() == "hello":
            await message.channel.send("Hi")
        
        # Check if the bot was mentioned
        elif self.user.mentioned_in(message):
            
            # TODO: Check if the triggered user is an admin
            # Clean the message (remove the <@ID> part)
            prompt = message.content.replace(f'<@!{self.user.id}>', '').replace(f'<@{self.user.id}>', '').strip()
            
            # If they just mentioned the bot with no text
            if not prompt:
                await message.channel.send("What? You need something or are you just staring?")
                return

            # Change state to "typing ..."
            async with message.channel.typing():
                # Trigger V.A.R.U.N.
                result = await self.public_agent.run(task=prompt)
                response = result.messages[-1].content
                
                # Send the result to Discord
                await message.reply(response)
        
        else:
            # TODO: Monitor for inappropriate/racist comments
            pass
        
        await self.process_commands(message)
        
        return

    ### PREFIX COMMANDS ###

    @commands.command(name="ping")
    # @bot.command(name="ping", help="Check the bot's latency")
    async def ping(self, ctx: commands.Context):
        """
        Simple prefix command that gets triggered on !ping and returns the apparent latency of the bot.
        """
        await ctx.send(f"> Pong! {round(self.latency * 1000)}ms")
        return

### SLASH COMMMANDS ###

# @bot.tree.command(name="yap", description="Talk to V.A.R.U.N.")
# @app_commands.describe(prompt="What do you want to ask V.A.R.U.N.?")
# async def yap(interaction: discord.Interaction, prompt: str):
#     """
#     Slash command that provides a simple chat interface with the V.A.R.U.N. agent
    
#     Args:
#         interaction (discord.Interaction): The interaction object that triggered this command.
#         prompt (str): User provided prompt
#     """
    
#     try:
#         # Load the "Thinking ..." message
#         await interaction.response.defer()
        
#         # Trigger the agent and asynchronously wait for the response
#         response = await bot.agent.run(task=prompt)
        
#         # Extract the text response
#         response = response.messages[-1].content
        
#         # Send the result back to Discord in chunks of 2000 characters
#         for i in range(0, len(response), 2000):
#             await interaction.followup.send(response[i:i + 2000])
    
#     except Exception as e:
#         await interaction.followup.send(f"Error: {e}")
    
#     return