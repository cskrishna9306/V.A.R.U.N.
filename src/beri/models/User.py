from pydantic import BaseModel

class User(BaseModel):
    """
    Models a user in the beri shared expense tracker.
    """
    id: int
    first_name: str
    last_name: str
    discord_username: str | None = ""