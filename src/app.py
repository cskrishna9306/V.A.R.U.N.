from fastapi import FastAPI, Response

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Success", "message": "Connection to varun.saichaparala.com is working!"}

@app.get("/health")
def health(response: Response):
    response.status_code = 200
    return {"status": "healthy"}
