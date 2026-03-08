import requests
import os
from dotenv import load_dotenv

load_dotenv()

NEBULA_KEY = os.getenv("NEBULA_API_KEY")
BASE_URL = "https://api.utdnebula.com"

print(f"Key loaded: '{NEBULA_KEY}'")
print(f"Key length: {len(NEBULA_KEY) if NEBULA_KEY else 0}")

# Try different auth formats
endpoints = ["/rooms", "/health", "/"]

for endpoint in endpoints:
    url = f"{BASE_URL}{endpoint}"
    
    # Try Bearer token
    r1 = requests.get(url, headers={"Authorization": f"Bearer {NEBULA_KEY}"}, timeout=5)
    print(f"\nGET {endpoint} with Bearer: {r1.status_code}")
    print(f"Response: {r1.text[:200]}")
    
    # Try x-api-key header instead
    r2 = requests.get(url, headers={"x-api-key": NEBULA_KEY}, timeout=5)
    print(f"GET {endpoint} with x-api-key: {r2.status_code}")
    print(f"Response: {r2.text[:200]}")
    
    # Try as query param
    r3 = requests.get(url, params={"api_key": NEBULA_KEY}, timeout=5)
    print(f"GET {endpoint} with ?api_key=: {r3.status_code}")
    print(f"Response: {r3.text[:200]}")