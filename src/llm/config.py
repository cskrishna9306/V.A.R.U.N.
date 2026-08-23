# Import standard packages
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Defines the LLM to use
# Bedrock inference profile ID for Claude Haiku 4.5
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

# AWS region hosting the Bedrock inference profile
AWS_REGION = os.getenv("AWS_REGION", "us-west-1")

# Load the GIPHY API key
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")

# Instantiate the GIPHY Base URL
GIPHY_BASE_SEARCH_URL = "https://api.giphy.com/v1/gifs/search"

# Define the number of GIFs to query for
GIPHY_SEARCH_LIMIT = 20

# Define the chance of querying GIPHY
# We retrieve GIFs only when the random number falls within this limit
# Higher the value, greater the chance of generating a GIF
GIF_LOTTERY = 0.5
