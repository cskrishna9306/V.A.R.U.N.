# Import Discord packages
import discord
from discord.ext import commands
from discord import app_commands

# Import custom packages
from src.llm.utils import get_gif
from src.beri import Beri
from src.discord.views.ClimaTact import ClimaTact

class Expense(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # Initialize the N.A.M.I. agent for expenses
        self.agent = bot.nami
        
        # Initialize the Beri object to be used via discord Views
        self.beri = Beri()

        return

    ### SLASH COMMANDS ###

    @app_commands.command(name="expense", description="Log a shared expense via N.A.M.I.")
    @app_commands.describe(
        prompt="Describe the expense, including amount, payer, participants, and optional group."
    )
    @app_commands.checks.has_role("Summoners")
    async def expense(self, interaction: discord.Interaction, prompt: str):
        """
        Slash command that routes an expense logging request to the N.A.M.I. agent.

        Args:
            interaction (discord.Interaction): The interaction object that triggered this command.
            prompt (str): Natural-language description of the expense.
        """

        try:
            # Acknowledge the interaction and show "Thinking..."
            await interaction.response.defer()

            # Trigger the N.A.M.I. agent and wait for the response
            result = self.agent.run(input=prompt)

            try:
                # Send the text result back to Discord in chunks of 2000 characters
                for i in range(0, len(result.text), 2000):
                    await interaction.followup.send(result.text[i : i + 2000])

                # Optionally send a GIF based on the gif_search_query
                gif_url = get_gif(result.gif_search_query)
                if gif_url:
                    await interaction.followup.send(gif_url)

            except Exception as e:
                # Fallback: if the LLM fails JSON formatting, just send the raw content
                print(f"Parsing error in /expense: {e}")
                await interaction.followup.send(result)

        except Exception as e:
            await interaction.followup.send(f"Error while logging expense: {e}")

        return

    @app_commands.command(name="bounty", description="Log a shared expense to Splitwise")
    @app_commands.checks.has_role("Summoners")
    async def bounty(self, interaction: discord.Interaction):
        """
        Slash command responsible for logging a shared expense to Splitwise.
        """
        
        # Initialize the ClimaTact view
        view = ClimaTact(self.beri)
        
        # Send the view to the channel
        await interaction.response.send_message(
            "Enter the expense description.",
            view=view,
        )
        
        return
    
# This is required for the bot to "load" the file
async def setup(bot: commands.Bot):
    await bot.add_cog(Expense(bot))

