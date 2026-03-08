import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes import ask

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="UTD Buddy Backend API",
    description="The logic layer for the UTD Buddy Godot application, integrated with Nebula API and Gemini.",
    version="1.0.0"
)

# Enable CORS for local Godot development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, change to the specific Origin that Godot runs on
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the UTD Buddy API!"}

app.include_router(ask.router)
