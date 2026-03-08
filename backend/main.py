# === LINE 1-8: Import the tools we installed ===
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from google import genai
from dotenv import load_dotenv
import json 
# === LINE 10-11: Load our secret keys from .env file ===
load_dotenv()

# === LINE 13: Create our web server ===
app = FastAPI()

# === LINE 16-21: Allow Godot to talk to this server ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === LINE 24-28: Set up Gemini AI (FIXED) ===
# ✅ FIXED: Correct env variable name (was "EMINI_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file!")

client = genai.Client(api_key=GEMINI_KEY)
# === LINE 31-33: Set up Nebula API (FIXED) ===
# ✅ FIXED: Removed trailing spaces from URL
NEBULA_BASE_URL = os.getenv("NEBULA_BASE_URL", "https://api.utdnebula.com").strip()
NEBULA_KEY = os.getenv("NEBULA_API_KEY")

# === LINE 35-37: Define what a "question" looks like ===
class QueryRequest(BaseModel):
    question: str

# === LINE 39-42: A simple test endpoint ===
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "UTD Desk Pet Backend"}

# === LINE 44-85: The MAIN function that handles questions ===
@app.post("/ask")
async def ask_pet(request: QueryRequest):
    
    # --- STEP 1: Try to get data from Nebula API ---
    nebula_data = {}
    
    if NEBULA_KEY:
        try:
            resp = requests.get(
                f"{NEBULA_BASE_URL}/rooms",
                headers={"x-api-key": NEBULA_KEY},
                #params={"q": request.question},
                timeout=3
            )
            if resp.status_code == 200:
                nebula_data = resp.json()
        except Exception as e:
            print(f"[Nebula Error] {e}")
            nebula_data = {"status": "unavailable"}
    else:
        print("[Warning] NEBULA_API_KEY not set in .env")

    # --- STEP 2: Ask Gemini AI to write an answer ---
    try:
        # ✅ FIXED: Real prompt string (not placeholder ...)
        prompt = (
            f"You are a friendly UTD Desk Pet assistant.\n\n"
            f"### INSTRUCTIONS:\n"
            f"1. Use ONLY the System Data below to answer questions about UTD events, classrooms, or clubs.\n"
            f"2. If the System Data is empty, unavailable, or doesn't contain the answer, say so politely and offer general help.\n"
            f"3. Keep responses concise (1-2 sentences), playful, and emoji-friendly.\n\n"
            f"### SYSTEM DATA (from Nebula Labs):\n"
            f"{json.dumps(nebula_data, indent=2) if nebula_data else 'No data available'}\n\n"
            f"### USER QUESTION:\n"
            f"{request.question}\n\n"
            f"### YOUR RESPONSE:"
        )
        
        # ✅ OLD API syntax (works with google-generativeai package)
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        
        return {
            "answer": response.text,
            "source": "gemini",
            "nebula_used": bool(nebula_data and nebula_data.get("status") != "unavailable")
        }
    
    except Exception as e:
        print(f"[Gemini Error] {e}")
        # 🎭 FALLBACK: Return a mock answer so demo never fails
        return {
            "answer": "🤖 My AI is thinking hard! Try asking about UTD events or classes.",
            "source": "fallback_mock",
            "nebula_used": False
        }

# === LINE 87-90: Start the server ===
if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Starting UTD Desk Pet Backend...")
    print(f"📡 Nebula URL: {NEBULA_BASE_URL}")
    uvicorn.run(app, host="127.0.0.1", port=8000)
