# Defines the LLM to use
MODEL_ID = "qwen2.5:latest"

# Construct the LLM config to pass to the agent
config_list = [
  {
    "model": MODEL_ID,
    "base_url": "http://localhost:11434/v1",
    # "api_key": "ollama",
  }
]