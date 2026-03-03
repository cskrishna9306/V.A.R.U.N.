# Import Discord packages
import discord
from discord.ext import commands

# Import custom packages
from src.llm.orchestrator import V_A_R_U_N
from src.discord.config import (
    ADMIN_TOOLS,
    BOIS_GUILD_ID,
    PUBLIC_TOOLS,
)
from src.models import YapResponse
from src.llm.utils import get_gif

class DiscordBot(commands.Bot):
    """
    The Discord Bot that utilizes the V.A.R.U.N. agent for fun and interactive conversations within a discord server.
    """
    
    def __init__(self):
        # Setup intents
        intents = discord.Intents.default()
        intents.presences = True
        intents.members = True
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
                
                try:
                    # Parse the JSON string into your Pydantic model
                    data = YapResponse.model_validate_json(response)
                    
                    # First, send the text message to Discord
                    await message.reply(data.text)
                    
                    # Call the get_gif tool
                    gif_url = get_gif(data.gif_search_query)
                    
                    # TODO: Maybe move the GIF lottery out of the get_gif routine
                    # Next, sent the GIF if the routine returned any
                    if gif_url:
                        await message.channel.send(gif_url)

                except Exception as e:
                    # Fallback: if the LLM fails JSON formatting, just send the raw content
                    print(f"Parsing error: {e}")
                    await message.reply(response)
        
        else:
            # TODO: Monitor for inappropriate/racist comments
            pass
        
        await self.process_commands(message)
        
        return

    async def on_member_join(self, member: discord.Member):
        """
        Method that gets triggered when a new member joins the server.

        Args:
            member (discord.Member): The member object that triggered this event.
        """
        # Avoid welcoming bots
        if member.bot:
            return
        
        # Get the system channel to send welcome messages to
        channel = member.guild.system_channel or discord.utils.get(member.guild.text_channels, name="general")
        
        if not channel:
            return
        
        # Change state to "typing ..."
        async with channel.typing():
            
            # Trigger V.A.R.U.N.
            result = await self.public_agent.run(task=f"System: New member {member.name} joined. Greet them with your usual blunt/sarcastic personality.")
            response = result.messages[-1].content
            
            try:
                # Parse the JSON string into your Pydantic model
                data = YapResponse.model_validate_json(response)
                
                # First, send the text message to Discord
                await channel.send(f'{member.mention} {data.text}')
                
                # Call the get_gif tool
                gif_url = get_gif(data.gif_search_query)
                
                # Next, sent the GIF if the routine returned any
                if gif_url:
                    await channel.send(gif_url)

            except Exception as e:
                # Fallback: if the LLM fails JSON formatting, just send the raw content
                print(f"Parsing error: {e}")
                await channel.send(response)
        
        return
    
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        """
        Triggered where there is an update in a member's status/presence.

        Args:
            before (discord.Member): The Member object before the update
            after (discord.Member): The Member object after the udpate
        """
        # Avoid reacting to bots
        if before.bot:
            return
        
        # DO NOT REACT to offline statuses
        if not after.activity:
            return
        
        # DO NOT REACT to the user not playing a game presently
        if not isinstance(after.activity, discord.Game):
            return
        
        # # Extract activity names safely
        # old_activity = before.activity.name if before.activity else None
        # new_activity = after.activity.name if after.activity else None

        # # Only proceed if the name actually changed
        # # This also catches the change of an activity change and NOT just a name change
        # # This is because names in the music/streaming/games are almost mutually exclusive
        # if old_activity == new_activity:
        #     return

        # Find the channel to send the response to
        channel = after.guild.system_channel or discord.utils.get(after.guild.text_channels, name="general")
        
        if not channel:
            return
        
        async with channel.typing():
            # Trigger V.A.R.U.N.
            # result = await self.public_agent.run(task=f"{after.name} switched from {before.activity.name if before.activity else 'doing nothing'} to {after.activity.name}. Roast them!")
            result = await self.public_agent.run(task=f"{after.name} is now playing {after.activity.name}. Roast them!")
            response = result.messages[-1].content
            
            try:
                # Parse the JSON string into your Pydantic model
                data = YapResponse.model_validate_json(response)
                
                # First, send the text message to Discord
                await channel.send(f"{after.mention} {data.text}")
                
                # Call the get_gif tool
                gif_url = get_gif(data.gif_search_query)
                
                # Next, send the GIF if the routine returned any
                if gif_url:
                    await channel.send(gif_url)
                
            except Exception as e:
                # Fallback: if the LLM fails JSON formatting, just send the raw content
                print(f"Parsing error: {e}")
                await channel.send(response)
            
        return