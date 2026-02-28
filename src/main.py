import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)  # commands.when_mentioned_or("!") is used to make the bot respond to !ping and @bot ping

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

bot.run(TOKEN)