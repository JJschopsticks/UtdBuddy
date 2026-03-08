# quick_test.py - Simple, reliable way to test your backend
import requests
import json

url = "http://127.0.0.1:8000/ask"

# Test questions - change this to test different bubbles
test_question = "What do you do?"
test_type = "general"  # "events", "classrooms", "custom", or "general"

data = {
    "question": test_question,
    "query_type": test_type
}

print(f"🤖 Asking: {test_question}")
print(f"📊 Query type: {test_type}")
print("-" * 50)

try:
    response = requests.post(url, json=data, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Success!")
        print(f"💬 Answer: {result['answer']}")
        print(f"🔗 Source: {result['source']}")
        print(f"📡 Nebula used: {result['nebula_used']}")
    else:
        print(f"❌ Server error: {response.status_code}")
        print(response.text)
        
except requests.exceptions.Timeout:
    print("❌ Request timed out (server might be busy)")
except requests.exceptions.ConnectionError:
    print("❌ Can't connect to server - is it running at http://127.0.0.1:8000?")
except Exception as e:
    print(f"❌ Error: {e}")
