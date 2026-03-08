import requests
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

NEBULA_KEY = os.getenv("NEBULA_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = "https://api.utdnebula.com"

print("=" * 50)
print("🔍 Testing Nebula...")
try:
    r = requests.get(f"{BASE_URL}/rooms", headers={"x-api-key": NEBULA_KEY}, timeout=5)
    if r.status_code == 200:
        print("✅ Nebula working!")
    else:
        print(f"❌ Nebula failed: {r.status_code} - {r.text[:100]}")
except Exception as e:
    print(f"❌ Nebula error: {e}")

print("=" * 50)
print("🔍 Testing Gemini...")
try:
    client = genai.Client(api_key=GEMINI_KEY)
    response = client.models.generate_content(model="gemini-2.0-flash-lite", contents="Say hello!")
    print(f"✅ Gemini working! Response: {response.text}")
except Exception as e:
    print(f"❌ Gemini error: {e}")

print("=" * 50)