# Import standard packages
from pydantic import BaseModel, Field
from typing import Any, Literal

class ToolCall(BaseModel):
    """
    Models the tool calls output by the planner agent.
    """
    name: Literal["get_friends", "get_groups", "log_expense"]
    args: dict[str, Any] = Field(default_factory=dict)