# Import Discord packages
import discord

# Import custom packages
from src.discord.views import ClimaTact

class DescriptionModal(discord.ui.Modal):
    """
    Modal to capture the expense description for the ClimaTact view.
    """
    
    def __init__(self, view: "ClimaTact"):
        """
        Initialize the DescriptionModal.

        Args:
            view (ClimaTact): The ClimaTact view to use.
        """
        super().__init__(title="Expense description")
        self._view = view

        self.description_input = discord.ui.TextInput(
            label="Description",
            style=discord.TextStyle.short,
            placeholder="What was this for?",
        )
        self.add_item(self.description_input)
        
        return

    async def on_submit(self, interaction: discord.Interaction):
        """
        Handle the submission of the modal.

        Args:
            interaction (discord.Interaction): The interaction object that triggered this modal.
        """
        try:
            # Get the description from the input
            # Remove any trailing characters
            desc = self.description_input.value.strip()
            if not desc:
                raise ValueError("Description cannot be empty.")
            
            # Update the internal desc variable in the view
            self._view.description = desc
            
            # Return control to the ClimaTact view
            await self._view.description_callback(interaction)
        
        except ValueError as e:
            # Transmit error message to the user
            await interaction.response.send_message(
                e,
                ephemeral=True,
            )
            # Transmit error message to the server
            print(f"Invalid description: {e}")
            
        except Exception as e:
            # Transmit error message to the user
            await interaction.response.send_message(
                "Error occurred while submitting the description modal.",
                ephemeral=True,
            )
            # Transmit error message to the server
            print(f"Error submitting the description modal: {e}")
        
        return
