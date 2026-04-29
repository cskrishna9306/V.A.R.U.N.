# Import standard packages
from pydantic import BaseModel, Field
from typing import Any, Literal

class ToolCall(BaseModel):
    """
    Models the tool calls output by the planner agent.
    """
    name: Literal["get_friends", "get_groups", "log_expense"] = Field(description="The tool to execute")
    args: dict[str, Any] = Field(description="The dictionary of arguments to pass to the tool to execute", default_factory=dict)