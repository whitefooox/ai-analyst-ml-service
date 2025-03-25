import uvicorn
from fastapi import FastAPI
from config import load_config


config = load_config()
app = FastAPI()

app.debug = config.debug


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
