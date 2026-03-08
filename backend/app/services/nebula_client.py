import os
import requests
import logging

logger = logging.getLogger(__name__)

class NebulaClient:
    def __init__(self):
        self.api_key = os.getenv("NEBULA_API_KEY")
        self.base_url = os.getenv("NEBULA_BASE_URL", "https://api.nebulalabs.com/v1")
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
    def _execute_query(self, endpoint: str, params: dict) -> dict:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            # The Nebula API returns a wrapper containing { "message": "success", "data": [...] }
            json_resp = response.json()
            if json_resp.get("message") == "success" and json_resp.get("data") is not None:
                return {"results": json_resp["data"]}
            else:
                return {"results": [], "message": "API returned no data"}
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401 or e.response.status_code == 403:
                logger.error("Nebula API Key is invalid or missing.")
            else:
                logger.error(f"Nebula Client error: {e.response.text}")
            return {"error": str(e), "details": e.response.text}
        except Exception as e:
            logger.error(f"Failed to connect to Nebula: {e}")
            return {"error": str(e), "message": "Failed to connect to Nebula. Service may be offline."}

    def search_course(self, params: dict) -> dict:
        """
        Queries the Nebula /course endpoint.
        Valid params include: subject_prefix, course_number, title
        """
        logger.info(f"Querying Nebula /course with {params}")
        return self._execute_query("course", params)
        
    def search_professor(self, params: dict) -> dict:
        """
        Queries the Nebula /professor endpoint.
        Valid params include: first_name, last_name
        """
        logger.info(f"Querying Nebula /professor with {params}")
        return self._execute_query("professor", params)


# Instantiate a single global client to use in our routes
nebula_client = NebulaClient()
