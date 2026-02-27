# import google.genai as genai
from google import genai
import os
from load_dotenv import load_dotenv

# # 1. Setup your API Key
# # Best practice: export GOOGLE_API_KEY="your-key-here" in your terminal
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# if not api_key:
#     print("Error: Please set the GOOGLE_API_KEY environment variable.")
#     exit(1)

# genai.configure()

# print(genai.list_models().models)
# # 2. Initialize the model
# # model = genai.GenerativeModel('gemini-1.5-flash')

# # # 3. Generate a response
# # prompt = "Explain why a Tesla T4 GPU is good for LLM inference in 2 sentences."

# # print(f"--- Sending Prompt: {prompt} ---")

# # response = model.generate_content(prompt)

# # print("\n--- Response ---")
# # print(response.text)

# import google.generativeai as genai

client = genai.Client(api_key=api_key)

# print(client.models.list().page)
response = client.models.generate_content(
    model="models/gemini-3-flash-preview",
    contents="Explain how AI works in a few words"
)
print(response.text)