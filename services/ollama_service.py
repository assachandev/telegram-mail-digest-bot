import logging
import requests

from .prompt_builder import build_system_prompt, build_user_prompt

logger = logging.getLogger(__name__)


class OllamaService:
    def __init__(self, host="http://localhost:11434", model="llama3.2:3b"):
        self.host = host.rstrip("/")
        self.model = model

    def summarize_emails(self, emails: list[dict]) -> str:
        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.model,
                    "stream": False,
                    "options": {"num_predict": 500},
                    "messages": [
                        {"role": "system", "content": build_system_prompt()},
                        {"role": "user", "content": build_user_prompt(emails)},
                    ],
                },
                timeout=600,
            )
            response.raise_for_status()
            return response.json()["message"]["content"].strip()
        except requests.exceptions.Timeout:
            raise TimeoutError("Ollama request timed out")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Cannot connect to Ollama at {self.host}")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise
