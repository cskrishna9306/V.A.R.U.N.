# Import standard packages
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Defines the LLM to use
# ChatOllama expects "<model>" instead of "ollama/<model>"
MODEL_ID = "qwen2.5:latest"

# Define the model provider's base URL
# localhost for locally hosted models via ollama
LLM_BASE_URL = "http://localhost:11434"

# Define the model provider API key
# ollama doest not require an API key, so we set a placeholder
MODEL_API_KEY = "ollama"

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
