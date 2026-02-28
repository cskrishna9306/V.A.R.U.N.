from fastapi import FastAPI
from pydantic import BaseModel
from src.gemini import client

app = FastAPI()

# 1. Define the schema
class ChatRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"status": "Success", "message": "Connection to varun.saichaparala.com is working!"}

@app.post("/talk")
def talk(
    query: ChatRequest
):
    response = client.models.generate_content(
        model="models/gemini-3-flash-preview",
        contents=query.query
    )
    return {"response": response.text}
    