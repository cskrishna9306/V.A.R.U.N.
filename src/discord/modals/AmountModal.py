# Import Discord packages
import discord

# Import custom packages
from src.discord.views import ClimaTact

class AmountModal(discord.ui.Modal):
    """
    Modal for entering the total amount of the expense.
    """
    def __init__(self, view: "ClimaTact"):
        """
        Initialize the modal.
        """
        super().__init__(title="Expense amount")
        self._view = view
        self.input_amount = discord.ui.TextInput(
            label="Total amount (USD)",
            placeholder="e.g. 42.50",
            required=True,
        )
        self.add_item(self.input_amount)
        
        return

    async def on_submit(self, interaction: discord.Interaction):
        """
        Submit the modal.
        """
        try:
            # Get the raw amount from the input
            # Sanitize the input by removing the $, , and any trailing characters
            raw = (
                self.input_amount.value.replace("$", "").replace(",", "").strip()
            )
            
            # Trying to convert the raw amount to a float will raise a ValueError when it encounters alphabets
            self._view.amount = float(raw)
            if self._view.amount <= 0:
                raise ValueError("Amount must be a positive number.")
            
            # Move to the amount callback step in ClimaTact view
            await self._view.amount_callback(interaction)
                    
        except ValueError as e:
            # Transmit error message to the user
            await interaction.response.send_message(
                e,
                ephemeral=True,
            )
            # Transmit error message to the server
            print(f"Invalid amount: {e}")
        
        except Exception as e:
            # Transmit error message to the user
            await interaction.response.send_message(
                "Error occurred while submitting the modal.",
                ephemeral=True,
            )
            # Transmit error message to the server
            print(f"Error submitting the modal: {e}")
        
        return