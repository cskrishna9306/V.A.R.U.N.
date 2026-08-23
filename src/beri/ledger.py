# Import standard packages
import logging
import random
from thefuzz import fuzz

# Import splitwise packages
from splitwise import Splitwise
from splitwise.expense import Expense

# Import custom packages
from src.beri.config import (
    SPLITWISE_CONSUMER_KEY,
    SPLITWISE_CONSUMER_SECRET,
    SPLITWISE_API_KEY,
)
from src.beri.models import User, SplitPolicy
from src.beri.exceptions import MissingGroupError
from src.beri.wall_street_journal import WSJ
from src.beri.utils import split_equally, create_expense_user

# Setup logging
logging.basicConfig(level=logging.DEBUG)

class Beri:
    def __init__(self):
        """
        Initialize the Beri object.
        """
        try:
            # Instantiate the journaling object
            self.wsj = WSJ()
            
            # Instantiate the Splitwise client on a per class basis
            self.splitwise_client = Splitwise(
                consumer_key=SPLITWISE_CONSUMER_KEY,
                consumer_secret=SPLITWISE_CONSUMER_SECRET,
                api_key=SPLITWISE_API_KEY,
            )
            
            # Log success message
            logging.info("Created the Splitwise client!")
            
            # Maintain state of the current user
            self._current_user = self.splitwise_client.getCurrentUser()
            
            # Maintain state on current user's friends
            self._friends = self.splitwise_client.getFriends()
            
            # Maintain state on current user's groups
            self._groups = self.splitwise_client.getGroups()
        
        except Exception as e:
            logging.error(f"Failed to create splitwise client: {e}")
        
        return
    
    def get_groups(self) -> list[str] | None:
        """
        Get a list of all the groups the user is part of.

        Returns:
            list[str] | None: A list of groups the user is part of
        """
        try:
            # Iterate over all the groups and extract the group name
            groups: list[str] = [
                group.name for group in self.splitwise_client.getGroups()
            ]
            
            logging.info("Retrieved all groups!")
            
            return groups
        
        except Exception as e:
            logging.error(f"Failed to retrieve groups: {e}")
        
        return
    
    def get_group_members(self, group_name: str) -> list[str] | None:
        """
        Get a list of all the members of a given group.
        
        Args:
            group_name (str): The name of the group to get the members of
        
        Returns:
            list[str] | None: A list of member names
        """
        try:
            # Get the group id for the group w/ the closest match to the provided name
            group_id = self.get_group_id(group_name)
            if not group_id:
                logging.error(f"Could not find group: {group_name}")
                return
            
            return [
                member.getFirstName() + ((" " + member.getLastName()) if member.getLastName() else "")
                for member in self.splitwise_client.getGroup(group_id).getMembers()
            ]
            
        except Exception as e:
            logging.error(f"Failed to retrieve group members: {e}")
            
        return
    
    def resolve_group(self, recipients: list[str]) -> list[str] | None:
        """
        Find a splitwise group encompassing majority if not all of the provided recipients.

        Args:
            recipients (list[str]): A list of recipient names to match against

        Returns:
            list[str] | None: A list of group names if found, else None
        """
        try:
            # A list of group names that encompass the provided recipients
            group_names: list[str] = []
            
            # Maintain a set of the provided recipients to perform subset matching
            # NOTE: Here, we only match on the first name of each recipient
            recipients = set(map(lambda x: x.lower().strip().split(" ")[0], recipients))
            
            # Iterate over all the groups and check if the recipients are part of any of them
            for group in self._groups:
                if recipients.issubset(set(member.getFirstName().lower().strip() for member in group.getMembers())):
                    group_names.append(group.getName())
            
            return group_names
        
        except Exception as e:
            logging.error(f"Failed to resolve group: {e}")
        
        return
    
    def get_friends(self) -> list[str] | None:
        """
        Get a list of the current user's friends (group-agnostic).
        
        Returns:
            list[str] | None: A list of friend names
        """
        try:
            # Construct and return the names of all friends to the current user
            return [
                user.getFirstName() + ((" " + user.getLastName()) if user.getLastName() else "")
                for user in self.splitwise_client.getFriends()
            ]
            
        except Exception as e:
            logging.error(f"Failed to retrieve the friends of {self._current_user}: {e}")
        
        return

    def add_transaction(
        self,
        amount: float,
        description: str,
        users: list[User],
        split_policy: SplitPolicy,
        group_id: int | None = None,
    ) -> int | None:
        """
        Public routine to add a transaction to splitwise.

        Args:
            amount (float): The total cost of the expense
            description (str): A description of the expense
            users (list[User]): List of users with paid_share and owed_share for each
            group_id (int | None): Optional group ID to attach the expense to

        Returns:
            int | None: The id of the Splitwise expense, or None on failure.
        """
        try:
            # Instantiate the splitwise Expense class w/ metadata
            expense = Expense()
            
            # Set the cost, description, and group ID of the expense
            expense.setCost(str(amount))
            expense.setDescription(description)
            
            # Set the group ID of the expense
            # NOTE: This is optional and will be set to None if not provided
            expense.setGroupId(group_id)
            
            # Set the users of the expense
            # expense.setUsers([self._user_to_expense_user(user) for user in users])
            expense.setUsers([create_expense_user(user) for user in users])
            
            # Set the split equally when necessary
            # Delegate the equal split to splitwise
            if split_policy == SplitPolicy.EQUAL:
                expense.setSplitEqually(True)

            # Initiate the splitwise expense/transaction
            expense, errors = self.splitwise_client.createExpense(expense)
            
            # Check for errors
            if errors:
                logging.error(f"Splitwise returned errors while creating expense: {errors.getErrors()}")
                return

            return expense.getId()
        
        except Exception as e:
            logging.error(f"Failed to add transaction: {e}")
        
        return
    
    def get_user_id(self, name: str) -> int | None:
        """
        Retrieve the Splitwise user ID for the provided user by searching friends and group members.

        Args:
            name (str): The full name of the user to search for

        Returns:
            int | None: The user id if a match is found, else None
        """
        try:
            # First we match on the entire name
            for user in [self._current_user] + self._friends:
                current_name = user.getFirstName() + (" " + user.getLastName() if user.getLastName() else "")
                if current_name == name:
                    return user.getId()
            
            # Otherwise, we perform fuzzy matching on the first and last name
            first_name = name.split(" ")[0].lower()
            last_name = name.split(" ")[1].lower() if len(name.split(" ")) > 1 else None

            # Build list: current user + friends + all group members (dedupe by id)
            seen_ids: set[int] = set()
            users: list = []

            for u in [self.splitwise_client.getCurrentUser()] + self.splitwise_client.getFriends():
                uid = u.getId()
                if uid not in seen_ids:
                    seen_ids.add(uid)
                    users.append(u)

            for group in self.splitwise_client.getGroups():
                for member in group.getMembers():
                    mid = member.getId()
                    if mid not in seen_ids:
                        seen_ids.add(mid)
                        users.append(member)

            best_match: tuple | None = None
            best_score = 0

            for user in users:
                u_first = (user.getFirstName() or "").lower()
                u_last = (user.getLastName() or "").lower()

                first_score = fuzz.ratio(u_first, first_name)
                if first_score < 80:
                    continue

                if last_name:
                    last_score = fuzz.ratio(u_last, last_name)
                    combined = (first_score + last_score) / 2
                else:
                    combined = first_score

                if combined > best_score:
                    best_score = combined
                    best_match = (user.getId(), combined)

            if best_match and best_match[1] >= 80:
                return best_match[0]

            logging.info(f"No match found for user: {first_name} {last_name or ''}")

        except Exception as e:
            logging.error(f"Failed to retrieve user Id for {name}: {e}")
        
        return
    
    # To log an expense:
    # 1. I'll create a pydantic model Transaction (to use instead of function parameters)
    # 2. Now, we need to enable multiple patrons as well
    # 2a. Each patron should have their shares too
    # 3. Figure out the split per recipient
    # 4. Given the list of patrons and recipients (if no group is given figure out a group with all of them)
    # 5. If a group is given, check if all patrons and recipients are part of it
    # 5a. splitwise handles this by default
    
    def log_expense(
        self,
        amount: float,
        description: str,
        patron: str,
        recipients: list[str],
        split_policy: SplitPolicy,
        recipient_shares: dict[str, float] | None = None,
        group_name: str | None = None,
    ) -> int | None:
        """
        High-level method to log an expense. Splits equally among participants.
        Payer pays the full amount; each participant owes their share.

        Args:
            amount (float): Total cost of the expense
            description (str): Description of the expense
            patron (str): First name of the person who paid
            recipients (list[str]): First names of all participants (including payer)
            recipient_shares (dict | None): The amount owed by each recipient, or None if the split policy is equal
            split_policy (SplitPolicy): The policy to use for splitting the expense
            group_name (str | None): Optional group name to attach the expense to

        Raises:
            MissingGroupError: If no group name is provided and no group is found encompassing all the recipients

        Returns:
            int | None: The Splitwise expense ID, or None on failure
        """
        try:
            if group_name:
                # Retrieve the group id for the group w/ the closest match to the provided name
                group_id = self.get_group_id(group_name)
            else:
                # Try to find a group encompassing all the provided recipients
                group_names = self.resolve_group(recipients)
                if not group_names:
                    raise MissingGroupError("No group found encompassing all the recipients")
                else:
                    raise MissingGroupError(f"Did you want to log this expense under any of the below group names? {group_names}")

            # Get the splitwise user ID of the patron
            patron_id = self.get_user_id(patron)
            if not patron_id:
                logging.error(f"Could not find user: {patron}")
                return

            # Build User list with paid/owed shares (equal split)
            num_recipients = len(recipients)
            if not num_recipients:
                logging.error("At least one recipient required")
                return
            
            # Instantiate the list of user objects to send to splitwise
            users: list[User] = []
            
            # Categorize debt evaluation by split policy and calculate owed shares
            match split_policy:
                
                case SplitPolicy.EQUAL:
                    # Implement the EQUAL split policy
                    # Here, each recipient owes an equal share to the patron
                    owed_shares = split_equally(amount, num_recipients)
                    
                    # NOTE: Here, we ensure that folks paying the remainder cents are randomized
                    random.shuffle(owed_shares)
                    
                    for i, recipient in enumerate(recipients):
                        user_id = self.get_user_id(recipient)
                        if not user_id:
                            logging.error(f"Could not find user: {recipient}")
                            return
                        
                        # Add the user to the list of users
                        users.append(
                            User(
                                id=user_id,
                                first_name=recipient,
                                last_name="",
                                paid_share=amount if recipient.lower() == patron.lower() else 0.0,
                                owed_share=owed_shares[i],
                            ),
                        )
                
                case SplitPolicy.AMOUNTS:
                    # Implemet the AMOUNT split policy
                    # We distribute debt based on the individual amounts owed by the recipients to the patron
                    
                    if not recipient_shares:
                        logging.error("No recipient shares provided for the AMOUNTS split policy")
                        return
                    
                    # First, check if the total amount in the recipient shares equals the total amount
                    if abs(sum([recipient_share for recipient_share in recipient_shares.values()]) - amount) > 0.01:
                        logging.error("Inconsistent share distribution. The total transaction amount differs more than 0.01 compared to the collective sum of individual recipient shares.")
                        return
                    
                    # Iterate over all the recepients (which includes the patron)
                    for recipient in recipients:
                        # Get the splitwise user ID of the recipient
                        user_id = self.get_user_id(recipient)
                        if not user_id:
                            logging.error(f"Could not find user: {recipient}")
                            return
                        
                        # Add the user to the list of users
                        users.append(
                            User(
                                id=user_id,
                                first_name=recipient,
                                last_name="",
                                paid_share=amount if recipient.lower() == patron.lower() else 0.0,
                                owed_share=recipient_shares[recipient], # Literally translates to the provided shares
                            ),
                        )
                                                        
                case SplitPolicy.PERCENTAGE:
                    # Implemet the PERCENTAGE split policy
                    # We distribute debt based on the individual percentage of the total amount owed by the recipients to the patron
                    
                    if not recipient_shares:
                        logging.error("No recipient shares provided for the PERCENTAGE split policy")
                        return
                    
                    # First, check if the total percentage in the recipient shares equals 100
                    if abs(sum([recipient_share for recipient_share in recipient_shares.values()]) - 100) > 0.01:
                        logging.error("Inconsistent share distribution. The collective percentage sum of individual recipient shares is not equal to 100!")
                        return
                    
                    # Iterate over all the recepients (which includes the patron)
                    for recipient in recipients:
                        # Get the splitwise user ID of the recipient
                        user_id = self.get_user_id(recipient)
                        if not user_id:
                            logging.error(f"Could not find user: {recipient}")
                            return
                        
                        # Add the user to the list of users
                        users.append(
                            User(
                                id=user_id,
                                first_name=recipient,
                                last_name="",
                                paid_share=amount if recipient.lower() == patron.lower() else 0.0,
                                owed_share=(recipient_shares[recipient] * amount) / 100 # Literally translates to the provided shares
                            ),
                        )

            # Add the transaction to the ledger
            expense_id = self.add_transaction(amount, description, users, split_policy, group_id)
            if not expense_id:
                logging.error("Failed to add transaction to ledger")
                return

            return expense_id
        
        except Exception as e:
            logging.error(f"Failed to log expense: {e}")
        
        return
    
    def log_expenses(self) -> int | None:
        """
        Public method to log/push the current state of the WSJ cache to Splitwise.
        
        Returns:
            int | None: The Splitwise expense ID, or None on failure
        """
        try:
            # How would we translate the debt graph in WSJ to splitwise expense?
            # We will need to figure out all the creditors and debtors first
            # The creditors will turn into patrons, and the debtors will turn into recipients
            
            # We will need to abstract the current debtors and creditors in the WSJ interface
            
            pass
        
        except Exception as e:
            logging.error(f"Failed to log expenses to Splitwise: {e}")
        
        return

    def get_group_id(self, group_name: str) -> int | None:
        """
        Retrieve the Splitwise group ID for the provided group name.

        Args:
            group_name (str): The group name to search for

        Returns:
            int | None: The group ID if found, else None
        """
        try:
            # Convert the provided group name into lowercase
            group_name = group_name.lower()
            
            # Maintain state on current user's groups
            self._groups = self.splitwise_client.getGroups()
            
            # A list of current user's group names that are similar to the provided group name
            similar_group_names: list[str] = []
            
            # Iterate over all of current user's groups
            for group in self._groups:
                
                # Check for an exact match
                if group.name.lower() == group_name:
                    logging.info("Found the correct group name!")
                    return group.getId()
                
                if fuzz.ratio(group.name.lower(), group_name) > 85:
                    similar_group_names.append(group.name)
                    
            logging.info(f"No match was found for {group_name}")
            
            # TODO: Just use fuzz.ratio() with a threshold
            if similar_group_names:
                print("Did you mean any of the below group names?")
                print(similar_group_names)
            
        except Exception as e:
            logging.error(f"Failed to retrieve the group Id for {group_name}")
            logging.error(e)
            
        return
    
    def _add_debt(self):
        pass
    
    def _update_debt(self):
        pass
    
    def _remove_debt(self):
        pass
    
    def __del__(self):
        """
        Cleanup method to close any open connections or perform any necessary cleanup.
        """
        # Currently, the splitwise client does not maintain an open connection, so no cleanup is necessary.
        # TODO: Ensure to log any journaled transactions from WSJ to splitwise!
        pass