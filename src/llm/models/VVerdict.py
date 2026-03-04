from pydantic import BaseModel

class VVerdict(BaseModel):
    """
    Models a regular response from V.A.R.U.N.
    """
    text: str
    gif_search_query: str | None