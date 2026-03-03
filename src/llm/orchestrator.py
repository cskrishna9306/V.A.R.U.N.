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
from src.models import YapResponse

class V_A_R_U_N(AssistantAgent):
    """
    The brain behind the V.A.R.U.N. discord bot.
    """
        
    def __init__(self, tools: list | None, response_format: BaseModel | None = YapResponse):
        super().__init__(
            name="V_A_R_U_N",
            system_message=load_system_prompt("V-A-R-U-N.md"),
            model_client=OllamaChatCompletionClient(
                model=MODEL_ID,
                response_format=response_format,
                model_info={
                    "vision": False,
                    "function_calling": True,
                    "json_output": True,
                }
            ),
            tools=tools
        )
        
        return

async def main():
    """
    Main function to run and test the V_A_R_U_N agent.
    """
    
    # Initialize the agent
    agent = V_A_R_U_N() 

    # Use the Console helper
    await Console(agent.run_stream(task="Translate 'I love coding' to emojis."))
    
    return

if __name__ == "__main__":
    asyncio.run(main())