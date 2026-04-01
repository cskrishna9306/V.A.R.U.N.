# Import standard packages
import logging
from thefuzz import fuzz
from splitwise import Splitwise
from splitwise.expense import Expense
from splitwise.user import ExpenseUser

# Import custom packages
from src.beri.config import (
    SPLITWISE_CONSUMER_KEY,
    SPLITWISE_CONSUMER_SECRET,
    SPLITWISE_API_KEY,
)
from src.beri.models import User
from src.beri.wall_street_journal import WSJ

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
    
    def _user_to_expense_user(self, user: User) -> ExpenseUser:
        """
        Helper method to convert our User model to Splitwise ExpenseUser.
        
        Args:
            user (User): The User model to convert

        Returns:
            ExpenseUser: The converted Splitwise ExpenseUser
        """
        
        try:
            # Instantiate the splitwise ExpenseUser class
            eu = ExpenseUser()
            
            # Set the ID, paid share, and owed share of the ExpenseUser
            eu.setId(user.id)
            eu.setPaidShare(str(user.paid_share))
            eu.setOwedShare(str(user.owed_share))
            
            # Return the converted Splitwise ExpenseUser
            return eu
        
        except Exception as e:
            logging.error(f"Failed to convert User to ExpenseUser: {e}")
        
        return

    def add_transaction(
        self,
        amount: float,
        description: str,
        users: list[User],
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
            expense.setUsers([self._user_to_expense_user(user) for user in users])

            # Initiate the splitwise expense/transaction
            expense, errors = self.splitwise_client.createExpense(expense)
            
            # Check for errors
            if errors:
                logging.error(f"Splitwise returned errors while creating expense: {errors}")
                return

            return expense.getId()

        except Exception as e:
            logging.error(f"Failed to add transaction: {e}")
        
        return
    
    def get_user_id(self, first_name: str, last_name: str | None = None) -> int | None:
        """
        Retrieve the Splitwise user ID for the provided user by searching friends and group members.

        Args:
            first_name (str): The first name of the user to search for
            last_name (str | None): Optional last name for disambiguation

        Returns:
            int | None: The user id if a match is found, else None
        """
        try:
            first_name = first_name.lower().strip()
            last_name = (last_name or "").lower().strip()

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
            logging.error(f"Failed to retrieve user Id for {first_name}: {e}")
        
        return
    
    def log_expense(
        self,
        amount: float,
        description: str,
        patron: str,
        recipients: list[str],
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
            group_name (str | None): Optional group name to attach the expense to

        Returns:
            int | None: The Splitwise expense ID, or None on failure
        """
        try:
            group_id = self.get_group_id(group_name) if group_name else None

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

            # Patron pays the full amount, each recipient owes their share
            owed_share = round(amount / num_recipients, 2)
            users: list[User] = []

            # Iterate over all the recepients
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
                        owed_share=owed_share,
                    ),
                )

            # Add the transaction to the ledger
            expense_id = self.add_transaction(amount, description, users, group_id)
            if not expense_id:
                logging.error("Failed to add transaction to ledger")
                return

            return expense_id
        
        except Exception as e:
            logging.error(f"Failed to log expense: {e}")
        
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