# Import standard packages
import logging

# Import custom packages
from src.beri.models import (
    Transaction,
    User,
    Debt,
    SplitPolicy,
)

# Setup logging
logging.basicConfig(level=logging.DEBUG)

class WSJ():
    """
    Python class that is supposed to embody a directed weighted graph for internal use by Beri.
    WSJ is the acronym for Wall Street Journal, and serves a similar functionality by keeping track of internal debt amongst friends.
    """
    
    def __init__(self):
        """
        Initialize the class state variables. It follows that of a simple graph.
        """
        # The set of all the users registered within the WSJ graph
        self.users: dict[int, User] = {}
        
        # Instantiate the adjacency list
        # The individual edges between all the users in the graph given all previous transactions
        self.debts: dict[int, dict[int, float]] = {}
        
        # Worst case, the adjacency list will consume O(n^2) space where n is the # of users
        # If we maintian an inverse/reversed graph to track credit we will consume another O(n^2) space
        self.credits: dict[int, dict[int, float]] = {}
        
        # Alternative, we keep track of the universal debt variable within each user class
        # +ve debt indicates debt, and -ve debt indicates credit
        # Additional space would be O(n), a new debt variable per user
        
        # How does this universal debt get updated?
        # When there is a new debt, from recipient -> patron
        # The debt of the RECIPIENT increases by new debt, and the debt of the PATRON decreases by new debt
        
        # Counter to keep track of the total number of transactions constituing the WSJ graph
        self.transactions: int = 0
        
        return
    
    def add_user(self, user: User) -> bool:
        """
        Public routine to add a new user vertice.
        
        Args:
            user (User): The user to add to the WSJ graph
        
        Returns:
            bool: True if the user was successfully to the state graph, False otherwise
        """
        try:
            # First, check if the user id is unique
            if user.id in self.users:
                logging.error(f"{user.id} already exists! Use another user id or update the existing user using WSJ.update_user() method.")
                return
            
            # Next, update the users state in WSJ
            self.users[user.id] = user
            
            return True
        
        except Exception as e:
            logging.error(f"Failed to create WSJ user: {e}")
        
        return False
    
    def update_user(self, user: User):
        """
        Public routine to update metadata surrounding an existing user. The user id CANNOT be modified.

        Args:
            user (User): The user details to update
        """
        pass
    
    def delete_user(self, user_id: int) -> bool:
        """
        Public method (for now) to delete a user from the WSJ graph.
        
        Args:
            user_id (int): The id of the user to delete from the WSJ graph
        
        Returns:
            bool: True if the user was successfully deleted from the state graph, False otherwise
        """
        try:
            # Check if this user exists in the list of all users
            if user_id not in self.users:
                logging.info(f"{user_id} does not exist in the current state of WSJ! Aborting deletion!")
                return True
            
            # For now, let's just clear the internal data structures of this user
            # NOTE: Need to figure out what to do with the debts of this user when deleting the user
            
            # Delete from the internal list of users
            del self.users[user_id]
            
            # Now, to delete all corresponding instances from the adjacency list
            for _, neighbors in self.debts.items():
                if user_id in neighbors:
                    del neighbors[user_id]
            
            # Finally, delete all debts owed by the provided user itself
            if user_id in self.debts:
                del self.debts[user_id]
            
            return True
        
        except Exception as e:
            logging.error(f"Failed to delete {user_id} from WSJ: {e}")
        
        return False
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """
        Public method to update the internal graph according to the provided transaction.

        Args:
            transaction (Transaction): The transaction to update the internal state of the graph
        """
        try:
            # NOTE: This subroutine assumes that ALL the users within the provided transaction already exist
            
            # Check if the provided transaction's patron exists in the WSJ graph
            if transaction.patron_id not in self.users:
                logging.error(f"The patron {transaction.patron_id} does not exist in the current WSJ graph.")
                return False
            
            # Check if all the recipients for this transaction exist in the WSJ graph
            if any(recipient_id not in self.users for recipient_id in transaction.recipient_ids):
                logging.error(f"At least 1 recipient is missing from the WSJ's internal state of users!")
                return False
            
            # Categorize debt evaluation, by split policy
            match transaction.split_policy:
                
                case SplitPolicy.EQUAL:
                    # Implement the EQUAL split policy
                    # Here, each recipient owes an equal share to the patron
                    
                    # We add an equal debt going from recipient -> patron
                    debt_amount: float = transaction.amount / len(transaction.recipient_ids)
                    
                    # Call the _add_debt() helper function to add the corresponding debt for each recipient to the patron
                    for recipient_id in transaction.recipient_ids:
                        if recipient_id != transaction.patron_id:
                            self._add_debt(
                                Debt(
                                    patron_id=transaction.patron_id,
                                    recipient_id=recipient_id,
                                    amount=debt_amount,
                                )
                            )
                
                case SplitPolicy.AMOUNTS:
                    # Implemet the AMOUNT split policy
                    # We distribute debt based on the individual amounts owed by the recipients to the patron
                    
                    # First, check if the total amount in the recipient shares equals the total amount
                    if abs(sum([recipient_share for recipient_share in transaction.recipient_shares.values()]) - transaction.amount) > 0.01:
                        logging.error("Inconsistent share distribution. The total transaction amount differs more than 0.01 compared to the collective sum of individual recipient shares.")
                        return False
                    
                    # Call the _add_debt() helper function to add the corresponding debt for each recipient to the patron
                    for recipient_id, recipient_share in transaction.recipient_shares.items():
                        if recipient_id != transaction.patron_id:
                            self._add_debt(
                                Debt(
                                    patron_id=transaction.patron_id,
                                    recipient_id=recipient_id,
                                    amount=recipient_share,
                                )
                            )
                                    
                case SplitPolicy.PERCENTAGE:
                    # Implemet the PERCENTAGE split policy
                    # We distribute debt based on the individual percentage of the total amount owed by the recipients to the patron
                    
                    # First, check if the total percentage in the recipient shares equals 100
                    if abs(sum([recipient_share for recipient_share in transaction.recipient_shares.values()]) - 100) > 0.01:
                        logging.error("Inconsistent share distribution. The collective percentage sum of individual recipient shares is not equal to 100!")
                        return False
                    
                    # Call the _add_debt() helper function to add the corresponding debt for each recipient to the patron
                    for recipient_id, recipient_share in transaction.recipient_shares.items():
                        if recipient_id != transaction.patron_id:
                            self._add_debt(
                                Debt(
                                    patron_id=transaction.patron_id,
                                    recipient_id=recipient_id,
                                    amount=(recipient_share * transaction.amount) / 100,
                                )
                            )
            
            # Increment the number of trasactions
            self.transactions += 1
            
            return True
        
        except Exception as e:
            logging.error(f"Failed to add the transaction: {e}")
            
        return False
    
    def _add_debt(self, debt: Debt) -> bool:
        """
        Private method to update the edges and their corresponding weights for the WSJ graph.

        Args:
            debt (Debt): The new debt to update the internal WSJ state with

        Returns:
            bool: True if provided debt was successfully added, False otherwise
        """
        try:
            # There is no need to check for uniqueness
            # NOTE: There can ONLY BE A SINGLE DEBT EDGE b/w any two users at a given point in time
            # NOTE: This enforces that a cycle in WSJ consists of at least 3 users (NO CYCLE W/ ONLY 2 users)
            # NOTE: A debt goes from the recepient to the patron
            
            # 3 possible states:
            # 1. If there is a debt edge from recipient to patron already, just update the weight
            # 2. If there is a debt edge from patron to recipient, check if the new weight switches the sign into negative
            #   2a. If there is no switch in the weight sign, just update the value (edge weight)
            #   2b. If there is a switch, remove the recipient from the patron's list of edges, and add the new edge to the recipient's list
            # 3. If there is no edge going either way, we add a new one
            
            # NOTE: Overall debt update is independent of the edge mappings
            # Update the global debt of both the patron and recipient
            self.users[debt.recipient_id].debt += debt.amount    # Increase in debt for the recipient
            self.users[debt.patron_id].debt -= debt.amount       # Decrease in debt for the patron
            
            if debt.patron_id in self.debts and debt.recipient_id in self.debts[debt.patron_id]:
                # Case 1: When there exists a debt edge from patron -> recipient (opposite direction)
                # We need to check if the new debt makes any state changes
                
                # Calculate net debt direction
                # The provided debt direction flows from RECIPIENT -> PATRON
                # However, current state has a debt direction of PATRON -> RECIPIENT
                net_debt = debt.amount - self.debts[debt.patron_id][debt.recipient_id]
                
                if net_debt > 0:
                    # There is a switch in the direction of debt
                    if debt.recipient_id not in self.debts:
                        self.debts[debt.recipient_id] = {}
                    
                    self.debts[debt.recipient_id][debt.patron_id] = net_debt
                    
                    # Clear the previous debt going from patron to recipient
                    del self.debts[debt.patron_id][debt.recipient_id]
                
                elif net_debt < 0:
                    # No switch, in overall debt (debt.amount < existing debt)
                    # Just update the current debt and move on
                    self.debts[debt.patron_id][debt.recipient_id] = -net_debt
                    
                else:
                    # Clear the edge when the net debt equates out
                    del self.debts[debt.patron_id][debt.recipient_id]
            
            else:
                # Case 2: When there already exists an edge going from recipient -> patron
                # Here, we just update the existing value w/ debt amount
                
                # Create a new edge
                if debt.recipient_id not in self.debts:
                    self.debts[debt.recipient_id] = {}
                
                # When there isn't an edge going from recipient -> patron, we create it
                if debt.patron_id not in self.debts[debt.recipient_id]:
                    self.debts[debt.recipient_id][debt.patron_id] = 0
                
                self.debts[debt.recipient_id][debt.patron_id] += debt.amount
            
            return True
        
        except Exception as e:
            logging.error(f"Failed to add debt: {e}")
            
        return False
    
    def get_user_debt(self, user_id: int) -> float | None:
        """
        Responsible for traversing the entire WSJ graph and returning the overall debt owed/to be owed to the provided user.

        Args:
            user_id (int): The user id to retrieve overall debt for

        Returns:
            float | None: The total debt owed/to be owed by the user, None otherwise
        """
        try:
            # Check if the given user id exists in the WSJ graph
            if user_id not in self.users:
                logging.error(f"The user with id {user_id} does not exist in the current WSJ graph.")
                return
            
            # Take the sum over all the outgoing edges from the provided user
            # return sum([self.debts[user_id].values()])
            return self.users[user_id].debt
        
        except Exception as e:
            logging.error(f"Failed to retrieve the debt for {user_id}: {e}")
        
        return
    
    def list_user_debt(self, user_id: int) -> list[Debt] | None:
        """
        Responsible for traversing the entire WSJ graph and returning the overall debt owed/to be owed to the provided user.

        Args:
            user_id (int): The user id to retrieve overall debt for

        Returns:
            list[Debt] | None: A list of overall debt and its recipients, None otherwise
        """
        try:
            # Check if the given user id exists in the WSJ graph
            if user_id not in self.users:
                logging.error(f"The user with id {user_id} does not exist in the current WSJ graph.")
                return
            
            # Get all outgoing edges from the provided user
            return [
                Debt(
                    patron_id=patron_id,
                    recipient_id=user_id,
                    amount=debt,
                ) for patron_id, debt in self.debts[user_id].items()
            ]
        
        except Exception as e:
            logging.error(f"Failed to retrieve the debt for {user_id}: {e}")
        
        return
    
    def settle_debt(self, patron_id: int, recipient_id: int) -> bool:
        """
        Public method to settle debt b/w the provided patron and recipient.

        Args:
            patron_id (int): The patron id
            recipient_id (int): The recipient id

        Returns:
            bool: True if the debt b/w the recipient and patron was successfully settled, False otherwise
        """
        try:
            # Check if both patron and recipient exist in the internal set of uses
            if patron_id not in self.users or recipient_id not in self.users:
                logging.error(f"Either {patron_id} or {recipient_id} does not exist within the current WSJ graph.")
                return False
            
            # Check if an edge exists from recipient to patron
            if recipient_id not in self.debts or patron_id not in self.debts[recipient_id]:
                logging.error(f"There is no existing debt from {recipient_id} to {patron_id}. Returning gracefully!")
                return True
            
            # Clear the debt b/w the patron and recipient
            del self.debts[recipient_id][patron_id]
            
            return True
        
        except Exception as e:
            logging.error(f"Failed to settle debt b/w {patron_id} and {recipient_id}: {e}")
            
        return False