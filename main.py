from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import mysql.connector
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

app = FastAPI()

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://369emon.github.io"],  # Replace with your GitHub Pages URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request models
class ChatRequest(BaseModel):
    message: str

class QueryRequest(BaseModel):
    query: str

class HistoryResponse(BaseModel):
    history: List[dict]

# Initialize Dolphin database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return connection
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database connection error: {err}")

# Initialize the database schema
def initialize_database():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            response TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    connection.commit()
    cursor.close()
    connection.close()

initialize_database()

# Helper function to call Replicate API
async def call_replicate(prompt):
    if not REPLICATE_API_TOKEN:
        raise HTTPException(status_code=500, detail="Replicate API token not found.")

    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "version": "meta/llama-2-7b-chat",  # Replace with the model version
        "input": {"prompt": prompt, "max_tokens": 512},
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 201:
        raise HTTPException(status_code=500, detail=f"Error calling Replicate API: {response.text}")

    prediction = response.json()
    prediction_id = prediction["id"]

    while True:
        result_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
        result_response = requests.get(result_url, headers=headers)
        result = result_response.json()

        if result["status"] == "succeeded":
            return "".join(result["output"])
        elif result["status"] == "failed":
            raise HTTPException(status_code=500, detail="Replicate API prediction failed")
        
        import time
        time.sleep(1)

# Endpoint for chat
@app.post("/chat")
async def chat(request: ChatRequest):
    prompt = f"My monarch commands: {request.message}"
    response = await call_replicate(prompt)

    # Store conversation in the database
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO conversation_history (title, response) VALUES (%s, %s)",
        (request.message, response.strip())
    )
    connection.commit()
    cursor.close()
    connection.close()

    return {"response": response.strip()}

# Endpoint for conversation history
@app.get("/history", response_model=HistoryResponse)
async def history():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT title, response, timestamp FROM conversation_history ORDER BY timestamp DESC")
    history = cursor.fetchall()
    cursor.close()
    connection.close()

    return {"history": history}

# Endpoint for file attachment
@app.post("/attach")
async def attach():
    return {"response": "File upload is not yet implemented, my monarch."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)