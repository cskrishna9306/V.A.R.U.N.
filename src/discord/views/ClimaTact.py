# Import discord packages
import asyncio
import discord

# Import custom packages
from src.beri import Beri
from src.beri.exceptions import MissingGroupError
from src.beri.models import SplitPolicy

_DISCORD_SELECT_MAX = 25


class AmountModal(discord.ui.Modal, title="Expense amount"):
    amount_input = discord.ui.TextInput(
        label="Total amount",
        placeholder="e.g. 42.50",
    )

    def __init__(self, view: "ClimaTact"):
        super().__init__()
        self._view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            raw = self.amount_input.value.replace("$", "").replace(",", "").strip()
            self._view.amount = float(raw)
            if self._view.amount <= 0:
                raise ValueError("positive")
        except ValueError:
            await interaction.response.send_message(
                "Invalid amount. Enter a positive number (e.g. 42.50).",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(DescriptionModal(self._view))


class DescriptionModal(discord.ui.Modal, title="Expense description"):
    description_input = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.short,
        placeholder="What was this for?",
    )

    def __init__(self, view: "ClimaTact"):
        super().__init__()
        self._view = view

    async def on_submit(self, interaction: discord.Interaction):
        desc = self.description_input.value.strip()
        if not desc:
            await interaction.response.send_message(
                "Description cannot be empty.",
                ephemeral=True,
            )
            return
        self._view.description = desc
        self._view.clear_items()
        self._view.build_split_policy_step()
        msg = self._view._format_progress(
            "Step 5: Select the split policy, then log the expense."
        )
        await interaction.response.edit_message(content=msg, view=self._view)


class ClimaTact(discord.ui.View):
    """
    Interactive Splitwise expense wizard.

    Flow:
        1. Choose a group
        2. Choose the recipients
        3. Enter the total amount (modal)
        4. Enter the description (modal)
        5. Select the split policy
        6. Log the expense (button)
    """

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
        self.split_policy: SplitPolicy | None = None
        self.group: str | None = None

        # Load the groups into the view
        self.load_groups()
        
        return

    def _format_progress(self, step_hint: str) -> str:
        lines = [step_hint, ""]
        if self.group:
            lines.append(f"Group: **{self.group}**")
        if self.recipients:
            lines.append(f"Recipients: **{', '.join(self.recipients)}**")
        if self.patron:
            lines.append(f"Paid by: **{self.patron}**")
        if self.amount is not None:
            lines.append(f"Amount: **{self.amount:.2f}**")
        if self.description:
            lines.append(f"Description: **{self.description}**")
        return "\n".join(lines)

    def load_groups(self) -> None:
        try:
            groups = self.beri.get_groups()
            if not groups:
                return
            options = [
                discord.SelectOption(label=g[:100], value=g[:100]) for g in groups
            ]
            select = discord.ui.Select(
                placeholder="Step 1: Choose the group",
                options=options,
                min_values=1,
                max_values=1,
            )
            select.callback = self.group_callback
            self.add_item(select)
        except Exception as e:
            print(f"Error loading groups: {e}")

    async def group_callback(self, interaction: discord.Interaction):
        self.group = interaction.data["values"][0]
        self.clear_items()
        members = self.beri.get_group_members(self.group)
        if not members:
            await interaction.response.edit_message(
                content=f"No members found for **{self.group}**. Try another group.",
                view=self,
            )
            return

        display = members[:_DISCORD_SELECT_MAX]
        note = ""
        if len(members) > _DISCORD_SELECT_MAX:
            note = f"\n_Showing the first {_DISCORD_SELECT_MAX} members._"

        options = [
            discord.SelectOption(label=m[:100], value=m[:100]) for m in display
        ]
        select = discord.ui.Select(
            placeholder="Step 2: Choose everyone splitting this expense",
            options=options,
            min_values=1,
            max_values=min(_DISCORD_SELECT_MAX, len(options)),
        )
        select.callback = self.recipients_callback
        self.add_item(select)
        await interaction.response.edit_message(
            content=self._format_progress(
                "Step 2: Choose the recipients."
            )
            + note,
            view=self,
        )

    async def recipients_callback(self, interaction: discord.Interaction):
        self.recipients = list(interaction.data["values"])
        self.clear_items()

        if len(self.recipients) == 1:
            self.patron = self.recipients[0]
            await interaction.response.send_modal(AmountModal(self))
            return

        options = [
            discord.SelectOption(label=r[:100], value=r[:100])
            for r in self.recipients
        ]
        select = discord.ui.Select(
            placeholder="Who paid?",
            options=options,
            min_values=1,
            max_values=1,
        )
        select.callback = self.patron_callback
        self.add_item(select)
        await interaction.response.edit_message(
            content=self._format_progress(
                "Pick who paid — next you will enter amount and description."
            ),
            view=self,
        )

    async def patron_callback(self, interaction: discord.Interaction):
        self.patron = interaction.data["values"][0]
        await interaction.response.send_modal(AmountModal(self))

    def build_split_policy_step(self) -> None:
        select = discord.ui.Select(
            placeholder="Step 5: Split policy",
            options=[
                discord.SelectOption(
                    label="Equal",
                    value="equal",
                    description="Split the total evenly among recipients",
                ),
                discord.SelectOption(
                    label="By exact amounts",
                    value="amounts",
                    description="Requires /expense or API — not in this wizard",
                ),
                discord.SelectOption(
                    label="By percentage",
                    value="percentage",
                    description="Requires /expense or API — not in this wizard",
                ),
            ],
            min_values=1,
            max_values=1,
        )
        select.callback = self.policy_callback
        self.add_item(select)

        btn = discord.ui.Button(
            label="Log expense",
            style=discord.ButtonStyle.green,
            row=1,
        )
        btn.callback = self.log_callback
        self.add_item(btn)

    async def policy_callback(self, interaction: discord.Interaction):
        raw = interaction.data["values"][0]
        self.split_policy = {
            "equal": SplitPolicy.EQUAL,
            "amounts": SplitPolicy.AMOUNTS,
            "percentage": SplitPolicy.PERCENTAGE,
        }[raw]
        await interaction.response.edit_message(
            content=self._format_progress(
                "Step 6: Click **Log expense** when ready."
            ),
            view=self,
        )

    async def log_callback(self, interaction: discord.Interaction):
        if self.split_policy is None:
            await interaction.response.send_message(
                "Choose a split policy first.",
                ephemeral=True,
            )
            return
        if self.split_policy is not SplitPolicy.EQUAL:
            await interaction.response.send_message(
                "Only **Equal** split is supported in this flow. Use `/expense` for custom splits.",
                ephemeral=True,
            )
            return
        if (
            self.amount is None
            or not self.description
            or not self.recipients
            or not self.patron
            or not self.group
        ):
            await interaction.response.send_message(
                "Something is missing — start over with `/bounty`.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        try:
            expense_id = await asyncio.to_thread(
                self.beri.log_expense,
                self.amount,
                self.description,
                self.patron,
                self.recipients,
                {},
                self.split_policy,
                self.group,
            )
        except MissingGroupError as e:
            await interaction.followup.send(f"Group error: {e}")
            return
        except Exception as e:
            await interaction.followup.send(f"Error: {e}")
            return

        if expense_id is None:
            await interaction.followup.send(
                "Splitwise did not return an expense id. Check the bot logs."
            )
            return

        self.clear_items()
        self.stop()
        await interaction.edit_original_response(
            content=f"**Expense logged** (id `{expense_id}`)\n{self._format_progress('')}",
            view=None,
        )
