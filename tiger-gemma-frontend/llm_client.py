import requests
from typing import Dict, Any

def get_server_url(public_ip: str, port: int) -> str:
    """Construct the server URL from IP and port."""
    return f"http://{public_ip}:{port}"

class LLMClient:
    def __init__(self, server_url: str):
        self.server_url = server_url

    def is_server_healthy(self) -> bool:
        """Check if the server is healthy."""
        try:
            response = requests.get(f"{self.server_url}/health")
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def generate_text(self, prompt: str, user_type: str, max_length: int, temperature: float, search_enabled: bool = False) -> Dict[str, Any]:
        """Generate text from the LLM via the server."""
        payload = {
            "prompt": prompt,
            "user_type": user_type,
            "max_length": max_length,
            "temperature": temperature,
            "search_enabled": search_enabled
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(f"{self.server_url}/generate", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
