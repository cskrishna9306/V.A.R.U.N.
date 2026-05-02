# Import Discord packages
import discord

# Import custom packages
from src.beri.models import SplitPolicy
from src.beri.exceptions import InconsistentSharesError, EmptySharesError
from src.discord.views import ClimaTact

class SharesModal(discord.ui.Modal):
    """
    Modal to capture the shares for each recipient for the ClimaTact view.
    The SharesModel is only triggered for non-equal split policies. (SplitPolicy.AMOUNTS or SplitPolicy.PERCENTAGE)
    """
    def __init__(self, view: "ClimaTact"):
        """
        Initialize the SharesModal.

        Args:
            view (ClimaTact): The ClimaTact view to use.
        """
        # Determine the modal_title
        modal_title = f"Amount owed (must sum to {view.amount:.2f})" if view.split_policy == SplitPolicy.AMOUNTS else f"Percentage shares owed (must sum to 100)"
        super().__init__(title=modal_title)
        self._view = view

        # Create one text input per recipient and keep references for on_submit.
        self.recipient_inputs = []
        for recipient in self._view.recipients:
            text_input = discord.ui.TextInput(
                label=recipient,
                style=discord.TextStyle.short,
                required=True,
            )
            self.recipient_inputs.append((recipient, text_input))
            self.add_item(text_input)
        
        return

    async def on_submit(self, interaction: discord.Interaction):
        """
        Handle the submission of the modal.
        This is triggered on the submission of the modal.

        Args:
            interaction (discord.Interaction): The interaction object that triggered this modal.
        """
        
        # What sort of input validation do I need here?
        # 1. All fields must be non-empty
        # 2. In case of amounts split policy, the total must sum to the amount
        # 3. In case of percentage split policy, the total must sum to 100
        
        try:
            # Get the shares from the modal
            shares = {
                recipient: text_input.value.replace("$", "").replace(",", "").strip()
                for recipient, text_input in self.recipient_inputs
            }
            
            # Validate the shares
            if not shares:
                raise EmptySharesError("No shares provided")
            
            # Convert the shares to floats
            shares = {
                recipient: float(share)
                for recipient, share in shares.items()
            }
            
            # Validate that the shares are non-negative
            if any(share < 0 for share in shares.values()):
                raise ValueError("Shares cannot be negative")
            
            # Validate that the sum of the shares equals the amount or 100
            if self._view.split_policy == SplitPolicy.AMOUNTS:
                if sum(shares.values()) != self._view.amount:
                    raise InconsistentSharesError("The total shares do not sum to the amount")
            elif self._view.split_policy == SplitPolicy.PERCENTAGE:
                if sum(shares.values()) != 100:
                    raise InconsistentSharesError("The total shares do not sum to 100")
            
            # Set the shares to the view
            self._view.recipient_shares = shares
            await self._view.shares_callback(interaction)
            
            return
        
        except EmptySharesError as e:
            await interaction.response.send_message(str(e))
            print(f"Empty shares: {e}")
        
        except InconsistentSharesError as e:
            await interaction.response.send_message(str(e))
            print(f"Inconsistent shares: {e}")
            
        except ValueError as e:
            await interaction.response.send_message(str(e))
            print(f"Invalid share value: {e}")
        
        except Exception as e:
            await interaction.response.send_message(str(e))
        
        return
