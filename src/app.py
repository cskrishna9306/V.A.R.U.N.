from fastapi import FastAPI
from src.gemini import client

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Success", "message": "Connection to varun.saichaparala.com is working!"}

@app.post("/talk")
def talk(
    prompt: str
):
    response = client.models.generate_content(
        model="models/gemini-3-flash-preview",
        contents=prompt
    )
    return {"response": response.text}
    