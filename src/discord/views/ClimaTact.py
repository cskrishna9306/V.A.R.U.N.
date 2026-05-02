# Import discord packages
import asyncio
import discord

# Import custom packages
from src.beri import Beri
from src.beri.exceptions import MissingGroupError, EmptyGroupError, ExpenseCreationError
from src.beri.models import SplitPolicy
from src.discord.modals import DescriptionModal, AmountModal, SharesModal

# Define the maximum number of options to display in a select menu
# This avoids overflowing the select menu
DISCORD_SELECT_MAX = 25

class ClimaTact(discord.ui.View):
    """
    Interactive Splitwise expense logging view.
    Provides a cleaner interactive interface for logging a shared expense to Splitwise.
    """
    
    # This view will provide the following flow:
    # 1. Enter the description
    # 2. Choose the group
    # 3. Choose the patron
    # 4. Choose the recipients
    # 5. Enter the total amount
    # 6. Select the split policy
    # 7. Anything other than equal split policy will require the user to enter the shares for each recipient
    # 8. Finally, log the expense

    def __init__(self, beri: Beri):
        """
        Initialize the ClimaTact view.

        Args:
            beri (Beri): The Beri object to use for the view.
        """
        # View timeout is 2 minutes
        super().__init__(timeout=120)
        
        # Initialize the Beri object
        self.beri = beri

        # Initialize the variables necessary to log an expense w/ splitwise
        self.amount: float | None = None
        self.description: str | None = None
        self.patron: str | None = None
        self.recipients: list[str] | None = None
        self.recipient_shares: dict[str, float] | None = None
        self.split_policy: SplitPolicy | None = None
        self.group: str | None = None
        self.group_members: list[str] = []

        # Start w/ getting the description from the user first
        self.add_description_step()
        
        return

    def add_description_step(self) -> None:
        """
        Add the description step to the view.
        """

        async def open_modal(interaction: discord.Interaction):
            await interaction.response.send_modal(DescriptionModal(self))

        btn = discord.ui.Button(
            label="Enter description for the expense",
            style=discord.ButtonStyle.primary,
        )
        btn.callback = open_modal
        self.add_item(btn)
        
        return

    def _format_progress(self, step_hint: str) -> str:
        lines = [step_hint, ""]
        if self.group:
            lines.append(f"Group: **{self.group}**")
        if self.patron:
            lines.append(f"Paid by: **{self.patron}**")
        if self.recipients:
            lines.append(f"Recipients: **{', '.join(self.recipients)}**")
        if self.amount is not None:
            lines.append(f"Amount: **{self.amount:.2f}**")
        if self.description:
            lines.append(f"Description: **{self.description}**")
        if self.split_policy is not None:
            lines.append(f"Split: **{self.split_policy.name}**")
        return "\n".join(lines)

    async def description_callback(self, interaction: discord.Interaction) -> None:
        """
        Handle the submission of the description modal.
        Follows the add_description_step.

        Args:
            interaction (discord.Interaction): The interaction object that triggered this callback.
        """
        try:
            # Clear the items from the view
            self.clear_items()
            
            # Get the groups from the Beri object
            groups = self.beri.get_groups()
            if not groups:
                raise MissingGroupError("No Splitwise groups found for your account.")

            options = [
                discord.SelectOption(label=group[:100], value=group[:100])
                for group in groups[:DISCORD_SELECT_MAX]
            ]
            
            # Create the select menu
            select = discord.ui.Select(
                placeholder="Choose the group",
                options=options,
                min_values=1,
                max_values=1,
            )
            select.callback = self.group_callback
            self.add_item(select)
            
            await interaction.response.edit_message(
                content=self._format_progress("Choose the group."),
                view=self,
            )
            
        except MissingGroupError as e:
            # Transmit error message to the user
            await interaction.response.edit_message(
                    content=e,
                    view=self,
                )
            # Transmit error message with the server
            print(f"No groups found: {e}")
            
        except Exception as e:
            # Transmit error message to the user
            await interaction.response.edit_message(
                    content="Error occurred while loading groups.",
                    view=self,
                )
            # Transmit error message with the server
            print(f"Error loading groups: {e}")
        
        return

    async def group_callback(self, interaction: discord.Interaction):
        """
        Group chosen -> select who paid (patron).
        """
        try:
            # Get the selected group from the previous step
            self.group = interaction.data["values"][0]
            self.clear_items()

            # Retrieve all group members from the selected group
            self.group_members = self.beri.get_group_members(self.group)
            if not self.group_members:
                raise EmptyGroupError(f"No members found for **{self.group}**.")
            
            # Create the options for the select menu
            options = [
                discord.SelectOption(label=member[:100], value=member[:100])
                for member in self.group_members[:DISCORD_SELECT_MAX]
            ]
            
            # Create the select menu
            select = discord.ui.Select(
                placeholder="Who paid?",
                options=options,
                # NOTE: Right now, we only allow one patron to be selected
                min_values=1,
                max_values=1,
            )
            select.callback = self.patron_callback
            self.add_item(select)

            await interaction.response.edit_message(
                content=self._format_progress("Choose who paid."),
                view=self,
            )

        except EmptyGroupError as e:
            # Transmit error message to the user
            await interaction.response.edit_message(
                content=e,
                view=self,
            )
            # Transmit error message to the server
            print(f"No members found for {self.group}: {e}")

        except Exception as e:
            # Transmit error message to the user
            await interaction.response.edit_message(
                content="Error occurred while loading recipients.",
                view=self,
            )
            # Transmit error message to the server
            print(f"Error loading recipients: {e}")
        
        return
    
    async def patron_callback(self, interaction: discord.Interaction):
        """
        Patron chosen -> select recipients splitting the expense.
        Follows the group_callback step.

        Args:
            interaction (discord.Interaction): The interaction object that triggered this callback.
        """
        try:
            # Get the selected patron from the previous step
            self.patron = interaction.data["values"][0]
            self.clear_items()

            # NOTE: The EmptyGroupError is handled in the group_callback

            # Create the options for the select menu
            options = [
                discord.SelectOption(label=member[:100], value=member[:100])
                for member in self.group_members[:DISCORD_SELECT_MAX]
            ]

            # Create the select menu
            select = discord.ui.Select(
                placeholder="Choose everyone splitting this expense",
                options=options,
                # Allows support for multiple recipients
                min_values=1,
                max_values=len(options),
            )
            select.callback = self.recipients_callback
            self.add_item(select)

            await interaction.response.edit_message(
                content=self._format_progress(
                    "Choose recipients."
                ),
                view=self,
            )
            
        except Exception as e:
            # Transmit error message to the user
            await interaction.response.edit_message(
                content="Error occurred while loading recipients.",
                view=self,
            )
            # Transmit error message to the server
            print(f"Error loading recipients: {e}")

        return

    async def recipients_callback(self, interaction: discord.Interaction):
        """
        Recipients chosen -> amount modal.
        """
        try:
            # Get the selected recipients from the patron_callback step
            self.recipients = list(interaction.data["values"])

            # Move on to the amount modal
            await interaction.response.send_modal(AmountModal(self))
        
        except Exception as e:
            # Transmit error message to the user
            await interaction.response.edit_message(
                content="Error occurred while loading recipients.",
                view=self,
            )
            # Transmit error message to the server
            print(f"Error loading recipients: {e}")
        
        return
    
    async def amount_callback(self, interaction: discord.Interaction):
        """
        Amount submitted -> split policy select.
        """
        try:
            # As usual, clear the items from the view
            self.clear_items()

            # Create the select menu
            select = discord.ui.Select(
                placeholder="Split policy",
                options=[
                    discord.SelectOption(
                        label="Equal",
                        value="equal",
                        description="Split evenly among recipients",
                    ),
                    discord.SelectOption(
                        label="By exact amounts",
                        value="amounts",
                        description="You will enter each person's share",
                    ),
                    discord.SelectOption(
                        label="By percentage",
                        value="percentage",
                        description="You will enter each person's percent",
                    ),
                ],
                # We can only choose one split policy
                min_values=1,
                max_values=1,
            )
            select.callback = self.split_policy_callback
            self.add_item(select)

            await interaction.response.edit_message(
                content=self._format_progress("Select the split policy."),
                view=self,
            )
        
        except Exception as e:
            # Transmit error message to the server
            await interaction.response.edit_message(
                content="Error occurred while loading split policy.",
                view=self,
            )
            # Transmit error message to the server
            print(f"Error loading split policy: {e}")
        
        return

    async def split_policy_callback(self, interaction: discord.Interaction):
        """
        Split policy chosen -> equal goes to log button; else we display the shares modal.
        """
        try:
            # Get the selected split policy from the previous step
            raw = interaction.data["values"][0]
            self.split_policy = {
                "equal": SplitPolicy.EQUAL,
                "amounts": SplitPolicy.AMOUNTS,
                "percentage": SplitPolicy.PERCENTAGE,
            }[raw]

            # Clear the items from the view
            self.clear_items()

            # Proceed to logging the expense if the split policy is equal
            if self.split_policy == SplitPolicy.EQUAL:
                await self.add_log_button()
                await interaction.response.edit_message(
                    content=self._format_progress("Click **Log expense** when ready."),
                    view=self,
                )
                
                return
            
            # Proceed to the shares modal for non-equal split policies
            await interaction.response.send_modal(SharesModal(self))
        
        except Exception as e:
            # Transmit error message to the server
            await interaction.response.edit_message(
                content="Error occurred while loading split policy.",
                view=self,
            )
            # Transmit error message to the server
            print(f"Error loading split policy: {e}")
        
        return

    async def shares_callback(self, interaction: discord.Interaction):
        """
        After shares modal (amount or percentage split): show log button.
        """
        try:
            # Clear the items from the view
            self.clear_items()
            
            # Add the log button to the view
            await self.add_log_button()
            
            # Edit the original message to show the log button
            await interaction.response.edit_message(
                content=self._format_progress("Click **Log expense** when ready."),
                view=self,
            )
        
        except Exception as e:
            # Transmit error message to the server
            await interaction.response.edit_message(
                content="Error occurred while adding the log button.",
                view=self,
            )
            # Transmit error message to the server
            print(f"Error adding the log button: {e}")
        
        return

    async def add_log_button(self) -> None:
        """
        Add the log button to the view.
        """
        # Create and add the log button to the view
        btn = discord.ui.Button(
            label="Log expense",
            style=discord.ButtonStyle.green,
        )
        btn.callback = self.log_callback
        self.add_item(btn)
        
        return

    async def log_callback(self, interaction: discord.Interaction) -> None:
        """
        Handle the submission of the log button.
        Follows the shares_callback step.

        Args:
            interaction (discord.Interaction): The interaction object that triggered this callback.
        """
        try:
            if not self.split_policy:
                raise ExpenseCreationError("No split policy selected.")
                
            if (
                self.amount is None
                or not self.description
                or not self.recipients
                or not self.patron
                or not self.group
            ):
                raise ExpenseCreationError("Something is missing — start over with `/bounty`.")

            await interaction.response.defer()
            
            # Call the Beri subroutine to log the expense in a separate thread
            expense_id = await asyncio.to_thread(
                self.beri.log_expense,
                self.amount,
                self.description,
                self.patron,
                self.recipients,
                self.split_policy,
                self.recipient_shares,  # Will be None for equal split policy
                self.group,
            )
            
            # Check for successful expense creation
            if not expense_id:
                await interaction.followup.send(
                    "Error while logging an expense to Splitwise."
                )
                raise ExpenseCreationError("Splitwise did not return an expense id.")
        
            # Clear the items from the view
            self.clear_items()
            self.stop()
            
            # Edit the original message to show the final receipt
            await interaction.edit_original_response(
                content=f"**Expense logged** (id `{expense_id}`)\n{self._format_progress('')}",
                view=None,
            )
            
            return
        
        except MissingGroupError as e:
            await interaction.followup.send(f"Failed to find group {self.group}: {e}")
        
        except ExpenseCreationError as e:
            await interaction.followup.send(f"Error while logging an expense to Splitwise: {e}")
        
        except Exception as e:
            await interaction.followup.send(f"Error: {e}")
        
        return
