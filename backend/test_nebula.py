# test_nebula.py - Test Nebula API directly (no Gemini)
import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Get Nebula credentials from .env
NEBULA_BASE_URL = os.getenv("NEBULA_BASE_URL", "https://api.utdnebula.com").strip()
NEBULA_KEY = os.getenv("NEBULA_API_KEY")

print("🔍 Testing Nebula Labs API")
print("=" * 50)
print(f"📡 Base URL: {NEBULA_BASE_URL}")
print(f"🔑 API Key: {NEBULA_KEY[:10]}..." if NEBULA_KEY else "❌ No API Key found!")
print("=" * 50)

if not NEBULA_KEY:
    print("❌ ERROR: NEBULA_API_KEY not found in .env file!")
    print("💡 Add this line to your .env file:")
    print("   NEBULA_API_KEY=your_key_here")
    exit(1)

# Test questions to try
test_queries = [
    "events",
    "hackathon",
    "classrooms",
    "study spaces",
    "clubs"
]

for query in test_queries:
    print(f"\n🔎 Testing query: '{query}'")
    print("-" * 50)
    
    try:
        # Make the API request
        url = f"{NEBULA_BASE_URL}/search"
        headers = {"Authorization": f"Bearer {NEBULA_KEY}"}
        params = {"q": query}
        
        print(f"📡 Request: GET {url}")
        print(f"📋 Params: {params}")
        
        response = requests.get(url, headers=headers, params=params, timeout=5)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Nebula returned data:")
            
            # Pretty print the JSON
            print(json.dumps(data, indent=2))
            
            # Check if data is actually useful
            if not data or data == {}:
                print("⚠️  Warning: Empty response (no data found)")
            elif isinstance(data, dict) and not any(data.values()):
                print("⚠️  Warning: Response has keys but no values")
            else:
                print("✅ Data looks valid!")
                
        elif response.status_code == 401:
            print("❌ 401 Unauthorized - API key might be invalid")
        elif response.status_code == 404:
            print("❌ 404 Not Found - URL or endpoint might be wrong")
        elif response.status_code == 403:
            print("❌ 403 Forbidden - API key doesn't have permission")
        elif response.status_code == 429:
            print("❌ 429 Too Many Requests - Rate limit hit")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (Nebula server might be slow)")
    except requests.exceptions.ConnectionError:
        print("❌ Can't connect to Nebula - check URL and internet")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
    
    print()  # Empty line between tests

print("=" * 50)
print("🏁 Nebula API testing complete!")
