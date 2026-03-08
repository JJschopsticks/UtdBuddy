# ============================================================================
# 🤖 UTD Desk Pet Backend - Two-Step Gemini Flow
# ============================================================================
# Flow: Question → Gemini(Intent) → Nebula → Gemini(Answer) → Godot
# ============================================================================

# === 1. IMPORTS ===
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import requests, os, json, logging
from datetime import date
from typing import Optional, Dict, Any, List
from google import genai
from dotenv import load_dotenv

# === 2. SETUP ===
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="UTD Desk Pet Backend", version="2.0.0")

# CORS: Allow Godot/frontend to call this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in .env")
gemini = genai.Client(api_key=GEMINI_KEY)

NEBULA_BASE = os.getenv("NEBULA_BASE_URL", "https://api.utdnebula.com").strip()
NEBULA_KEY = os.getenv("NEBULA_API_KEY")

# === 3. REQUEST MODEL ===
class UserQuestion(BaseModel):
    question: str = Field(default="", max_length=2000)
    
    @field_validator('question')
    @classmethod
    def clean(cls, v: str) -> str:
        return v.strip() if v.strip() else "What can I help you with today?"

# === 4. HEALTH CHECK ===
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "UTD Desk Pet Backend v2.0",
        "nebula": bool(NEBULA_KEY),
        "gemini": bool(GEMINI_KEY)
    }

# ============================================================================
# 🧠 STEP 1: GEMINI AS INTENT CLASSIFIER
# ============================================================================

INTENT_SCHEMA = """
You are an intent classifier for UT Dallas data queries.

### VALID INTENTS & ENDPOINTS:
- "events"    → /events/{date}[/building[/room]]
- "rooms"     → /rooms
- "clubs"     → /club/search[?q=...]
- "courses"   → /course[?q=...] or /astra/{date}[/building]
- "professors"→ /professor[?q=...]
- "grades"    → /grades/overall or /course/{id}/grades
- "discounts" → /discountPrograms
- "calendar"  → /calendar/{date}[/building]
- "mazevo"    → /mazevo/{date}
- "unknown"   → /rooms (fallback)

### PARAMETER RULES:
- date: "YYYY-MM-DD" format only (e.g., "2024-03-15")
- building: 2-4 letter UTD code: SU, EC, FO, JS, SL, GR, MC, PO, RH, SG, PN, MS
- room: Building+number, NO SPACE: "SU2402" (not "SU 2.402")
- course: DEPT+NUMBER, NO SPACE: "CS1337" (not "CS 1337")
- q: Search keyword for /club/search, /course, /professor

### OUTPUT FORMAT (STRICT JSON ONLY):
{
  "intent": "events|rooms|clubs|courses|professors|grades|discounts|calendar|mazevo|unknown",
  "endpoint": "/exact/endpoint/path",
  "params": {"date": "2024-03-15", "building": "SU", "room": "SU2402", "course": "CS1337"},
  "query_params": {"q": "search_term"},
  "confidence": 0.0-1.0
}

Return ONLY valid JSON. No markdown, no explanations.
"""

def classify_intent_with_gemini(question: str) -> Dict[str, Any]:
    """
    Send user question to Gemini → Get structured intent classification.
    Returns dict with: intent, endpoint, params, query_params, confidence
    """
    today = date.today().isoformat()
    
    prompt = (
        f"{INTENT_SCHEMA}\n\n"
        f"### TODAY'S DATE: {today}\n\n"
        f"### USER QUESTION: \"{question}\"\n\n"
        f"### YOUR JSON RESPONSE:"
    )
    
    try:
        logger.info(f"🧠 Classifying intent: '{question[:80]}...'")
        
        response = gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"temperature": 0.1, "max_output_tokens": 300}
        )
        
        # Parse JSON from response
        raw = response.text.strip()
        
        # Handle markdown code blocks
        if raw.startswith("```"):
            raw = raw.split("```")[1] if "```" in raw else raw
            if raw.startswith("json"): raw = raw[4:]
            raw = raw.strip()
        
        # Extract JSON object
        start = raw.find('{')
        end = raw.rfind('}') + 1
        if start >= 0 and end > start:
            raw = raw[start:end]
        
        result = json.loads(raw)
        
        # Validate required fields
        required = ["intent", "endpoint", "confidence"]
        if not all(k in result for k in required):
            logger.warning(f"⚠️ Gemini intent response missing fields: {result.keys()}")
            return _default_intent_classification(question)
        
        # Normalize types
        result["confidence"] = float(result.get("confidence", 0.0))
        result["params"] = result.get("params", {}) or {}
        result["query_params"] = result.get("query_params", {}) or {}
        
        logger.info(f"✅ Classified: intent={result['intent']}, endpoint={result['endpoint']}, conf={result['confidence']:.2f}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Intent classification failed: {e}")
        return _default_intent_classification(question)


def _default_intent_classification(question: str) -> Dict[str, Any]:
    """Fallback intent classifier when Gemini fails"""
    q = question.lower()
    today = date.today().isoformat()
    
    # Simple keyword matching fallback
    if any(k in q for k in ['event', 'hackathon', 'workshop']):
        return {"intent": "events", "endpoint": f"/events/{today}", "params": {"date": today}, "query_params": {}, "confidence": 0.5}
    elif any(k in q for k in ['room', 'study', 'classroom', 'available']):
        return {"intent": "rooms", "endpoint": "/rooms", "params": {}, "query_params": {}, "confidence": 0.6}
    elif any(k in q for k in ['club', 'organization']):
        return {"intent": "clubs", "endpoint": "/club/search", "params": {}, "query_params": {"q": "student"}, "confidence": 0.5}
    else:
        return {"intent": "unknown", "endpoint": "/rooms", "params": {}, "query_params": {}, "confidence": 0.3}


# ============================================================================
# 📡 STEP 2: FETCH DATA FROM NEBULA API
# ============================================================================

def fetch_nebula_data(endpoint: str, query_params: Dict = None) -> Dict:
    """Call Nebula API and return JSON data"""
    if not NEBULA_KEY or not endpoint:
        return {"error": "API not configured" if not NEBULA_KEY else "No endpoint"}
    
    url = f"{NEBULA_BASE}{endpoint}"
    headers = {"x-api-key": NEBULA_KEY}
    params = {k: v for k, v in (query_params or {}).items() if v is not None}
    
    try:
        logger.info(f"📡 Nebula GET: {url} | params: {params or 'none'}")
        
        resp = requests.get(url, headers=headers, params=params if params else None, timeout=8)
        
        if resp.status_code == 200:
            data = resp.json()
            logger.info(f"✅ Nebula success: {len(json.dumps(data))} bytes")
            return data
        else:
            error_text = resp.text[:200] if resp.text else "No response body"
            logger.warning(f"⚠️ Nebula {resp.status_code}: {error_text}")
            return {"error": f"API returned {resp.status_code}", "details": error_text}
            
    except requests.exceptions.Timeout:
        logger.error("❌ Nebula timeout")
        return {"error": "timeout"}
    except Exception as e:
        logger.error(f"❌ Nebula fetch error: {e}")
        return {"error": str(e), "type": type(e).__name__}


# ============================================================================
# 🤖 STEP 3: GEMINI AS ANSWER GENERATOR
# ============================================================================

def generate_final_answer(question: str, nebula_data: Dict, intent: str) -> str:
    """
    Send user question + Nebula data to Gemini → Get natural language answer.
    """
    # Prepare data context (truncate if too large)
    data_json = json.dumps(nebula_data, default=str, indent=2)
    if len(data_json) > 12000:
        data_json = data_json[:12000] + "\n...[truncated for length]..."
    
    prompt = (
        f"You are a friendly, knowledgeable UTD Desk Pet assistant! 🤖✨\n\n"
        f"### YOUR ROLE:\n"
        f"• Answer using ONLY the System Data below.\n"
        f"• If data is missing/empty/error, politely say so and suggest alternatives.\n"
        f"• Keep answers SHORT (1-3 sentences), playful, and emoji-friendly.\n"
        f"• Quote times, rooms, names ACCURATELY from the data.\n"
        f"• NEVER make up information not in the System Data.\n\n"
        f"### CONTEXT: intent={intent}\n\n"
        f"### SYSTEM DATA (from Nebula API):\n```json\n{data_json}\n```\n\n"
        f"### USER QUESTION: {question}\n\n"
        f"### YOUR RESPONSE (concise, friendly, accurate):"
    )
    
    try:
        logger.info("🤖 Generating answer with Gemini...")
        
        response = gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"temperature": 0.3}
        )
        
        return response.text.strip()
        
    except Exception as e:
        logger.error(f"❌ Answer generation failed: {e}")
        # Context-aware fallbacks
        fallbacks = {
            "events": "🎪 Having trouble fetching events! Try UTD's official events page or ask about a specific date.",
            "rooms": "🏫 Room data is updating. Pro tip: SU and EC usually have open study spaces during weekdays!",
            "clubs": "🎭 Club directory is buffering. Visit CometConnect for the full list of UTD student organizations!",
            "courses": "📚 Course info is loading. Try asking with a specific course code like 'CS 1337'!",
            "professors": "👨‍🏫 Professor data is updating. Try 'Who teaches CS 1337?' for better results!",
            "grades": "📊 Grade statistics are refreshing. Ask about a specific course for details!",
            "discounts": "💰 Discount info is loading. Check the UTD student deals page for current offers!",
            "default": "🤖 My brain is buffering! Try rephrasing your question about UTD events, classes, or campus life."
        }
        return fallbacks.get(intent, fallbacks["default"])


# ============================================================================
# 🎯 MAIN ENDPOINT: /ask (The Complete Flow)
# ============================================================================

@app.post("/ask")
async def handle_question(request: UserQuestion):
    """
    Complete Two-Step Gemini Flow:
    
    1️⃣ User question → Backend
    2️⃣ Backend → Gemini (Intent Classifier)
    3️⃣ Gemini → Returns {intent, endpoint, params}
    4️⃣ Backend → Calls Nebula API with that endpoint
    5️⃣ Nebula → Returns JSON data
    6️⃣ Backend → Sends (question + data) → Gemini (Answer Generator)
    7️⃣ Gemini → Returns natural language answer
    8️⃣ Backend → Returns answer to Godot ✅
    """
    
    user_question = request.question
    logger.info(f"\n🧠 New Question: '{user_question}'")
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 1: Gemini classifies intent → returns endpoint info
    # ═══════════════════════════════════════════════════════════════════
    intent_result = classify_intent_with_gemini(user_question)
    
    intent = intent_result.get("intent", "unknown")
    endpoint = intent_result.get("endpoint", "/rooms")
    params = intent_result.get("params", {})
    query_params = intent_result.get("query_params", {})
    confidence = intent_result.get("confidence", 0.0)
    
    logger.info(f"🎯 Intent: {intent} (confidence: {confidence:.2f})")
    logger.info(f"🔗 Endpoint: {endpoint}")
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 2: Backend calls Nebula API with the classified endpoint
    # ═══════════════════════════════════════════════════════════════════
    nebula_data = fetch_nebula_data(endpoint, query_params)
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 3: Gemini generates final answer using question + Nebula data
    # ═══════════════════════════════════════════════════════════════════
    final_answer = generate_final_answer(user_question, nebula_data, intent)
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 4: Return structured response to Godot
    # ═══════════════════════════════════════════════════════════════════
    return {
        "answer": final_answer,                              # 🎯 Natural language response
        "source": "gemini",                                  # Answer source
        "nebula_used": "error" not in nebula_data,           # Did Nebula call succeed?
        "metadata": {                                        # Debug/development info
            "intent": intent,
            "endpoint": endpoint,
            "confidence": confidence,
            "params": params,
            "query_params": query_params,
            "nebula_status": "ok" if "error" not in nebula_data else nebula_data.get("error")
        }
    }


# ============================================================================
# 🚀 SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 70)
    print("🚀 UTD Desk Pet Backend v2.0 - Two-Step Gemini Flow")
    print("=" * 70)
    print(f"📡 Nebula API: {NEBULA_BASE} | {'✅' if NEBULA_KEY else '❌'}")
    print(f"🤖 Gemini AI:  {'✅' if GEMINI_KEY else '❌'}")
    print("=" * 70)
    print("🔄 Flow: Question → Gemini(Intent) → Nebula → Gemini(Answer) → Godot")
    print("=" * 70)
    print("📚 Supported Intents:")
    print("   🎪 events    → /events/{date}[/building[/room]]")
    print("   🚪 rooms     → /rooms")
    print("   🎭 clubs     → /club/search[?q=...]")
    print("   📚 courses   → /course[?q=...] or /astra/{date}[/building]")
    print("   👨‍🏫 professors → /professor[?q=...]")
    print("   📊 grades    → /grades/overall or /course/{id}/grades")
    print("   💰 discounts → /discountPrograms")
    print("   📅 calendar  → /calendar/{date}[/building]")
    print("   🗓️ mazevo    → /mazevo/{date}")
    print("=" * 70)
    print("🌐 Server: http://127.0.0.1:8000")
    print("💡 Test: curl -X POST http://127.0.0.1:8000/ask -H 'Content-Type: application/json' -d '{\"question\":\"Events today?\"}'")
    print("=" * 70 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
