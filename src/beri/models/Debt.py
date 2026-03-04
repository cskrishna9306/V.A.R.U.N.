from pydantic import BaseModel

class Debt(BaseModel):
    """
    Models the debt between 2 users of the beri system.
    """
    patron_id: int
    recipient_id: int
    amount: float