import os
import json
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configure Gemini globally
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    logger.warning("GEMINI_API_KEY is not set in the environment. AI generation will fail.")

# Define a system prompt that gives UTD Buddy its character and instructions
SYSTEM_PROMPT = """
You are UTD Buddy, an AI-powered desktop assistant designed specifically for students at the University of Texas at Dallas (UTD).
You are a friendly, helpful, and knowledgeable robot mascot.

Your job is to answer user questions using the context provided from the Nebula API.
When given Nebula search results, prioritize that information to construct your answer.
If the Nebula context does not contain enough information or is empty, you may use your general knowledge, but clearly state that you are making an assumption or suggest the user check official UTD resources.

Keep your answers conversational, concise, and helpful. Output ONLY the answer text, do not include markdown or JSON formatting in your final response text unless necessary for readability.
"""

ROUTER_PROMPT = """
You are an intelligent router for UTD Buddy. Your job is to extract search parameters from a user's question so we can query the UTD Nebula API.
The Nebula API has two main endpoints: "course" and "professor".

Analyze the user's question and output ONLY a valid JSON object matching this schema:
{
  "endpoint": "course" | "professor" | "none",
  "params": {
    // If endpoint is "course", extract one or more:
    // "subject_prefix": (e.g., "CS", "ACCT", "MATH", "HIST")
    // "course_number": (e.g., "4349", "2301", "1326")
    // "title": (e.g., "Advanced Algorithm Design", "Introductory Financial Accounting")
    
    // If endpoint is "professor", extract one or more:
    // "first_name": (e.g., "John", "Jason", "Karen")
    // "last_name": (e.g., "Fell", "Smith", "Mazidi")
  }
}

If the user is asking a general question not related to courses or professors, set endpoint to "none".
Do not wrap your response in markdown blocks like ```json. Output raw JSON only.
"""

class AIWrapper:
    def __init__(self):
        # We use the gemini-pro model for generation
        self.model = genai.GenerativeModel('gemini-pro')
        
    def extract_intent(self, question: str) -> dict:
        """
        Passes the question to Gemini to extract route params.
        Returns a dict like {"endpoint": "course", "params": {"subject_prefix": "CS", "course_number": "4349"}}
        """
        combined_prompt = f"{ROUTER_PROMPT}\n\nUser Question:\n{question}\n\nJSON Output:"
        try:
            if not os.getenv("GEMINI_API_KEY"):
                # Fallback directly to no context if no key is configured
                return {"endpoint": "none", "params": {}}
                
            response = self.model.generate_content(combined_prompt)
            raw_text = response.text.strip()
            # In case the model accidentally replies with markdown
            if raw_text.startswith("```json"):
                raw_text = raw_text.split("```json")[-1]
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[-1]
            if raw_text.endswith("```"):
                raw_text = raw_text.rsplit("```", 1)[0]
                
            return json.loads(raw_text.strip())
        except Exception as e:
            logger.error(f"Failed to extract intent with Gemini: {e}")
            return {"endpoint": "none", "params": {}}

    def generate_response(self, question: str, nebula_context: dict) -> str:
        """
        Generates a natural-language answer by combining the user's question,
        the structured data from Nebula, and the system prompt.
        """
        
        # We format the Nebula Context to a clean JSON string so Gemini can read it easily
        context_str = json.dumps(nebula_context, indent=2)
        
        # We combine the system prompt, context, and the user's question into a single prompt for Gemini
        combined_prompt = f"{SYSTEM_PROMPT}\n\nNebula API Context:\n{context_str}\n\nUser Question:\n{question}\n\nAnswer:"
        
        try:
            if not os.getenv("GEMINI_API_KEY"):
                return "I couldn't process your question because my GEMINI_API_KEY is missing from the .env file! Please add it and restart the server."
                
            response = self.model.generate_content(combined_prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Failed to generate response with Gemini: {e}")
            return f"I'm sorry, my brain (Gemini) encountered an error processing your request: {e}"

# Instantiate a single global wrapper
ai_wrapper = AIWrapper()
