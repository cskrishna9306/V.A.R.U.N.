from pydantic import BaseModel

class User(BaseModel):
    """
    Models a user in the beri shared expense tracker.
    """
    id: int
    name: str
    discord_username: str | None