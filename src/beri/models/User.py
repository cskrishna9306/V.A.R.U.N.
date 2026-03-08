from pydantic import BaseModel

class User(BaseModel):
    """
    Models a user in the beri shared expense tracker.
    """
    id: int
    first_name: str
    last_name: str
    paid_share: float
    owed_share: float
    discord_username: str | None