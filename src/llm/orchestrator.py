# Import standard packages
import asyncio
from pydantic import BaseModel

# Import autogen packages
from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ModelFamily
from autogen_ext.models.anthropic import AnthropicBedrockChatCompletionClient, BedrockInfo
from autogen_agentchat.ui import Console

# Import custom packages
from src.llm.config import AWS_REGION, MODEL_ID
from src.llm.utils import load_system_prompt
from src.llm.models import VVerdict

class V_A_R_U_N(AssistantAgent):
    """
    The brain behind the V.A.R.U.N. discord bot.
    """

    def __init__(self, tools: list | None, response_format: BaseModel | None = VVerdict):
        super().__init__(
            name="V_A_R_U_N",
            system_message=load_system_prompt("V-A-R-U-N.md"),
            model_client=AnthropicBedrockChatCompletionClient(
                model=MODEL_ID,
                response_format=response_format,
                model_info={
                    "vision": False,
                    "function_calling": True,
                    "json_output": True,
                    "family": ModelFamily.CLAUDE_3_5_HAIKU,
                    "structured_output": True,
                },
                # No explicit keys: falls back to the standard AWS credential
                # chain (env vars, shared config/profile, or IAM role).
                bedrock_info=BedrockInfo(
                    aws_region=AWS_REGION,
                ),
            ),
            tools=tools
        )
        
        return

async def main():
    """
    Main function to run and test the V_A_R_U_N agent.
    """
    # Import here to avoid circular import (orchestrator <-> discord)
    from src.discord.config import PUBLIC_TOOLS

    # Initialize the agent with public tools
    agent = V_A_R_U_N(tools=PUBLIC_TOOLS) 

    # Use the Console helper
    await Console(agent.run_stream(task="Translate 'I love coding' to emojis."))
    
    return

if __name__ == "__main__":
    asyncio.run(main())