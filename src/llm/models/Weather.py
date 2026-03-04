from pydantic import BaseModel

class Weather(BaseModel):
    """
    Models a weather report
    """
    temperature: float
    condition: str