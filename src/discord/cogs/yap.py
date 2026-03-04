# Import Discord packages
import discord
from discord.ext import commands
from discord import app_commands

# Import custom packages
from src.llm.models import VVerdict
from src.llm.utils import get_gif

class Yap(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Initialize the V.A.R.U.N. agent
        self.agent = bot.public_agent
        
        return
    
    ### PREFIX COMMANDS ###

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """
        Simple prefix command that gets triggered on !ping and returns the apparent latency of the bot.
        """
        await ctx.send(f"> Pong! {round(self.bot.latency * 1000)}ms")
        return
    
    ### SLASH COMMANDS ###
    
    @app_commands.command(name="yap", description="Talk with V.A.R.U.N.")
    @app_commands.describe(prompt="What do you want to ask V.A.R.U.N.?")
    async def yap(self, interaction: discord.Interaction, prompt: str):
        """
        Slash command that provides a simple chat interface with the V.A.R.U.N. agent
        
        Args:
            interaction (discord.Interaction): The interaction object that triggered this command.
            prompt (str): User provided prompt
        """
        
        try:
            # Load the "Thinking ..." message
            await interaction.response.defer()
            
            # Trigger the agent and asynchronously wait for the response
            response = await self.agent.run(task=prompt)
            
            # Extract the text response
            response = response.messages[-1].content
                
            try:
                # Parse the JSON string into your Pydantic model
                data = VVerdict.model_validate_json(response)
                
                # First, send the text result back to Discord in chunks of 2000 characters
                for i in range(0, len(data.text), 2000):
                    await interaction.followup.send(data.text[i:i + 2000])
                
                # Call the get_gif tool
                gif_url = get_gif(data.gif_search_query)
                
                # Next, sent the GIF if the routine returned any
                if gif_url:
                    await interaction.followup.send(gif_url)

            except Exception as e:
                # Fallback: if the LLM fails JSON formatting, just send the raw content
                print(f"Parsing error: {e}")
                await interaction.followup.send(response)
        
        except Exception as e:
            await interaction.followup.send(f"Error: {e}")
        
        return

# This is required for the bot to "load" the file
async def setup(bot):
    await bot.add_cog(Yap(bot))