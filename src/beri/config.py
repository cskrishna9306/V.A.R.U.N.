# Import standard packages
import os
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

# Instantiate the Splitwise API credentials
SPLITWISE_CONSUMER_KEY = os.getenv("SPLITWISE_CONSUMER_KEY")
SPLITWISE_CONSUMER_SECRET = os.getenv("SPLITWISE_CONSUMER_SECRET")
SPLITWISE_API_KEY = os.getenv("SPLITWISE_API_KEY")