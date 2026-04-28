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
    
    recipient_ids: list[int]
    split_policy: SplitPolicy
    
    # A dictionary mapping each recepient and their respective share amount
    recipient_shares: dict[int, float] | None = {}
    
    # Splitwise group id for associated namespace mapping
    group_id: int | None = None
    