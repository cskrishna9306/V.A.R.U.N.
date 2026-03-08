# Import Discord packages
import discord
from discord.ext import commands
from discord import app_commands

# Import custom packages
from src.llm.models import VVerdict
from src.llm.utils import get_gif


class Expense(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # Initialize the N.A.M.I. agent for expenses
        self.agent = bot.nami

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
            result = await self.agent.run(task=prompt)

            # Extract the text response
            response = result.messages[-1].content

            try:
                # Parse the JSON string into the shared VVerdict model
                data = VVerdict.model_validate_json(response)

                # Send the text result back to Discord in chunks of 2000 characters
                for i in range(0, len(data.text), 2000):
                    await interaction.followup.send(data.text[i : i + 2000])

                # Optionally send a GIF based on the gif_search_query
                gif_url = get_gif(data.gif_search_query)
                if gif_url:
                    await interaction.followup.send(gif_url)

            except Exception as e:
                # Fallback: if the LLM fails JSON formatting, just send the raw content
                print(f"Parsing error in /expense: {e}")
                await interaction.followup.send(response)

        except Exception as e:
            await interaction.followup.send(f"Error while logging expense: {e}")

        return


# This is required for the bot to "load" the file
async def setup(bot: commands.Bot):
    await bot.add_cog(Expense(bot))

