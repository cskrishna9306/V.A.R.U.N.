# Import standard packages
import logging

# Import splitwise packages
from splitwise.user import ExpenseUser

# Import custom packages
from src.beri.models import User

# Setup logging
logging.basicConfig(level=logging.DEBUG)

def create_expense_user(user: User) -> ExpenseUser:
    """
    Helper method to create a Splitwise ExpenseUser from a User model.
    
    Args:
        user (User): The User model to create an ExpenseUser from

    Returns:
        ExpenseUser: The created Splitwise ExpenseUser
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

def split_equally(total: float, n: int) -> list[float]:
    """
    Split total dollars into n equal parts; returned values sum exactly to total.
    This helper function ensures that the total sum of the shares equals the total amount and redistributes the remainder cents to the recipients.
    """
    if n <= 0:
        raise ValueError("The total # of recipients must be positive")
    
    # Convert the total to cents and split equally
    total_cents = int(round(total * 100))
    base_cents = total_cents // n
    remainder_cents = total_cents % n

    # Return the list of equal shares w/ remainder distribution
    return [
        (base_cents + (1 if i < remainder_cents else 0)) / 100.0
        for i in range(n)
    ]