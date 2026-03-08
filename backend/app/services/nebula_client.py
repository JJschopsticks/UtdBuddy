import os
import requests
import logging

logger = logging.getLogger(__name__)

class NebulaClient:
    def __init__(self):
        self.api_key = os.getenv("NEBULA_API_KEY")
        self.base_url = os.getenv("NEBULA_BASE_URL", "https://api.nebulalabs.com/v1")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def search(self, query: str) -> dict:
        """
        Queries the Nebula API with the given string.
        Returns the JSON response from Nebula.
        """
        # Note: If the actual Nebula search endpoint is different from /search,
        # adjust this URL path accordingly.
        url = f"{self.base_url}/search"
        params = {"q": query}
        
        try:
            # We add a timeout so the request to Gemini doesn't hang indefinitely if Nebula is down
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # You might want to pass these up, but for now we just return an error dict 
            # to let Gemini know that Nebula data retrieval failed.
            if e.response.status_code == 401:
                logger.error("Nebula API Key is invalid or missing.")
            else:
                logger.error(f"Nebula Client error: {e}")
            return {"error": str(e), "message": "Could not retrieve context from Nebula"}
        except Exception as e:
            logger.error(f"Failed to connect to Nebula: {e}")
            return {"error": str(e), "message": "Failed to connect to Nebula. Service may be offline."}

# Instantiate a single global client to use in our routes
nebula_client = NebulaClient()
