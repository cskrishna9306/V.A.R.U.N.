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
    debt: float | None = 0.0    # Overall debt owed by this user: +ve implies debt, -ve implies credit
    discord_username: str | None = ""