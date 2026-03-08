# Import standard packages
import asyncio
from pydantic import BaseModel

# Import autogen packages
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_agentchat.ui import Console

# Import custom packages
from src.llm.config import MODEL_ID
from src.llm.utils import load_system_prompt
from src.llm.models import VVerdict

class N_A_M_I(AssistantAgent):
    """
    Shared expense / Splitwise specialist agent that uses Beri tools.
    """

    def __init__(self, tools: list | None, response_format: BaseModel | None = VVerdict):
        super().__init__(
            name="N_A_M_I",
            system_message=load_system_prompt("N-A-M-I.md"),
            model_client=OllamaChatCompletionClient(
                model=MODEL_ID,
                response_format=response_format,
                model_info={
                    "vision": False,
                    "function_calling": True,
                    "json_output": True,
                },
            ),
            tools=tools,
        )

        return


async def main():
    """
    Main function to run and test the N.A.M.I. agent.
    """
    # Import here to avoid circular import (accountant <-> discord)
    from src.discord.config import BERI_TOOLS

    # Initialize the agent with tools (Beri expense logging)
    agent = N_A_M_I(tools=BERI_TOOLS)
    
    # Use the Console helper
    await Console(agent.run_stream(task="Log an expense for $2 for dinner with Sai and Monniiesh in Shut My Ass group with Sai paying for the bill."))
    
    return

if __name__ == "__main__":
    asyncio.run(main())
