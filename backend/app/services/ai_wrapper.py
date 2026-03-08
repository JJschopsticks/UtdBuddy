import os
import json
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configure Gemini globally
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Define a system prompt that gives UTD Buddy its character and instructions
SYSTEM_PROMPT = """
You are UTD Buddy, an AI-powered desktop assistant designed specifically for students at the University of Texas at Dallas (UTD).
You are a friendly, helpful, and knowledgeable robot mascot.

Your job is to answer user questions using the context provided from the Nebula API.
When given Nebula search results, prioritize that information to construct your answer.
If the Nebula context does not contain enough information, you may use your general knowledge, but clearly state that you are making an assumption or suggest the user check official UTD resources.

Keep your answers conversational, concise, and helpful. Output ONLY the answer text, do not include markdown or JSON formatting in your final response text unless necessary for readability.
"""

class AIWrapper:
    def __init__(self):
        # We use the gemini-pro model as requested
        self.model = genai.GenerativeModel('gemini-pro')

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
            response = self.model.generate_content(combined_prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Failed to generate response with Gemini: {e}")
            return f"I'm sorry, my brain (Gemini) encountered an error processing your request: {e}"

# Instantiate a single global wrapper
ai_wrapper = AIWrapper()
