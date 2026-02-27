from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Success", "message": "Connection to varun.saichaparala.com is working!"}
