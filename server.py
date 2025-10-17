from fastapi import FastAPI

# Create a FastAPI application instance
app = FastAPI()

# Define a root endpoint that responds to GET requests
@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# Define an endpoint with a path parameter
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}