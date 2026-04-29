# Import standard packages
from pydantic import BaseModel, Field

# Import custom modules
from .ToolCall import ToolCall

class NVerdict(BaseModel):
    """
    Models the final verdict from the NAMI agent.
    """
    text: str = Field(description="The final response summarizing the execution of the NAMI agent")
    tool_calls: list[ToolCall] | None = Field(description="The tool calls used verbatim from the planning phase")
    gif_search_query: str | None = Field(description="The search keywords used for querying for a GIF")