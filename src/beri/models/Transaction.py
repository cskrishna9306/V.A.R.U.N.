# Import standard packages
from pydantic import BaseModel

# Import custom packages
from src.beri.models import SplitPolicy

class Transaction(BaseModel):
    """
    Models a shared transaction among beri users.
    """
    description: str
    amount: float
    patron_id: int
    
    recepient_ids: list[int]
    split_policy: SplitPolicy
    
    # A dictionary mapping each recepient and their respective share amount
    recepient_shares: dict[int, float]
    