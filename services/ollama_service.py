import logging
import requests
import time

from .prompt_builder import build_system_prompt, build_user_prompt

logger = logging.getLogger(__name__)


class OllamaService:
    def __init__(self, host="http://localhost:11434", model="llama3.2:3b"):
        self.host = host.rstrip("/")
        self.model = model
        self.is_available = True
        self.last_check_time = 0
        self.check_interval = 5  # Check every 5 seconds
        self.retry_attempts = 3
        self.retry_delay = 2  # seconds

    def is_healthy(self) -> bool:
        """Check if Ollama is available."""
        current_time = time.time()
        # Only check every 5 seconds to avoid excessive requests
        if current_time - self.last_check_time < self.check_interval:
            return self.is_available

        try:
            response = requests.get(
                f"{self.host}/api/tags",
                timeout=5,
            )
            response.raise_for_status()
            self.is_available = True
            self.last_check_time = current_time
            return True
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            self.is_available = False
            self.last_check_time = current_time
            return False
        except Exception as e:
            logger.error(f"Ollama health check error: {e}")
            self.is_available = False
            self.last_check_time = current_time
            return False

    def summarize_emails(self, emails: list[dict]) -> str:
        """Summarize emails with automatic retry on connection failure."""
        last_error = None

        for attempt in range(self.retry_attempts):
            try:
                # Check if Ollama is available before making request
                if not self.is_healthy():
                    if attempt < self.retry_attempts - 1:
                        logger.warning(
                            f"Ollama unavailable, retrying in {self.retry_delay}s "
                            f"(attempt {attempt + 1}/{self.retry_attempts})"
                        )
                        time.sleep(self.retry_delay)
                    continue

                response = requests.post(
                    f"{self.host}/api/chat",
                    json={
                        "model": self.model,
                        "stream": False,
                        "options": {"num_predict": 1500},
                        "messages": [
                            {"role": "system", "content": build_system_prompt()},
                            {"role": "user", "content": build_user_prompt(emails)},
                        ],
                    },
                    timeout=600,
                )
                response.raise_for_status()
                self.is_available = True
                return response.json()["message"]["content"].strip()

            except requests.exceptions.Timeout:
                last_error = TimeoutError("Ollama request timed out")
                if attempt < self.retry_attempts - 1:
                    logger.warning(
                        f"Ollama timeout, retrying in {self.retry_delay}s "
                        f"(attempt {attempt + 1}/{self.retry_attempts})"
                    )
                    time.sleep(self.retry_delay)

            except requests.exceptions.ConnectionError as e:
                last_error = ConnectionError(f"Cannot connect to Ollama at {self.host}")
                self.is_available = False
                if attempt < self.retry_attempts - 1:
                    logger.warning(
                        f"Ollama connection error, retrying in {self.retry_delay}s "
                        f"(attempt {attempt + 1}/{self.retry_attempts})"
                    )
                    time.sleep(self.retry_delay)

            except Exception as e:
                last_error = e
                logger.error(f"Ollama error: {e}")
                if attempt < self.retry_attempts - 1:
                    logger.warning(
                        f"Retrying in {self.retry_delay}s "
                        f"(attempt {attempt + 1}/{self.retry_attempts})"
                    )
                    time.sleep(self.retry_delay)

        # All retries exhausted
        if last_error:
            raise last_error
        raise ConnectionError(f"Cannot connect to Ollama at {self.host}")
