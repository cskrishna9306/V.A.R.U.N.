# Import standard packages
import os
from dotenv import load_dotenv

# Import Discord packages
import discord
from discord.ext import commands
from discord import app_commands

# Import custom packages
from src.llm.orchestrator import V_A_R_U_N

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        # 1. Setup Intents (Must have Message Content for non-slash, 
        # but Slash commands work via 'Interactions')
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        
        self.agent = V_A_R_U_N()  # Initialize the V.A.R.U.N. agent

    async def setup_hook(self):
        # This copies your commands to your specific server for instant updates
        # Replace 'GUILD_ID' with your actual Server ID
        MY_GUILD = discord.Object(id=1294893602568409128) 
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)
        print("Slash commands synced!")

bot = MyBot()

@bot.event
async def on_ready() -> None:  # This event is called when the bot is ready
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message: discord.Message) -> None:  # This event is called when a message is sent
    if message.author.bot:  # If the message is sent by a bot, return
        return

    if message.content == "Hello":  # If the message content is Hello, respond with Hi
        await message.channel.send("Hi")

    await bot.process_commands(message)  # This is required to process commands

@bot.command()
async def ping(ctx: commands.Context) -> None:  
    await ctx.send(f"> Pong! {round(bot.latency * 1000)}ms")

# @bot.slash_command()
# async def talk(ctx: commands.Context, *, query: str) -> None:
#     response = client.models.generate_content(
#         model="models/gemini-3-flash-preview",
#         contents=query
#     )
#     await ctx.send(response.text)
    
# @bot.tree.command(name="talk", description="Send a prompt to V.A.R.U.N.")
# # @app_commands.describe(prompt="What do you want to ask?")
# async def talk(interaction: discord.Interaction, prompt: str):
#     """
#     'prompt' is the variable that captures the text 
#     the user types after /talk
#     """
#     # Defer the response if your AI takes more than 3 seconds to think
#     await interaction.response.defer()
    
#     # logic: Here is where you'd call Gemini or your local vLLM
#     response_text = client.models.generate_content(
#         model="models/gemma-3-4b-it",
#         contents=prompt
#     ).text
    
#     # Followup is used because we 'deferred' earlier
#     await interaction.followup.send(response_text)
@bot.tree.command(name="talk", description="Send a prompt to V.A.R.U.N. via Local Ollama")
@app_commands.describe(prompt="What do you want to ask?")
async def talk(interaction: discord.Interaction, prompt: str):
    # 1. Defer immediately (Local LLMs on a T4 take a few seconds to generate)
    await interaction.response.defer()
    
    try:
        response = await bot.agent.run(task=prompt)
        
        response_text = response.messages[-1].content
        
    except Exception as e:
        response_text = f"Error contacting local Ollama: {str(e)}"
    
    # 3. Send the result back to Discord
    # Note: Discord has a 2000 character limit per message
    if len(response_text) > 2000:
        await interaction.followup.send(response_text[:1990] + "...")
    else:
        await interaction.followup.send(response_text)

bot.run(TOKEN)