from abc import ABC, abstractmethod


class BaseMailService(ABC):
    @abstractmethod
    def authenticate(self):
        pass

    @abstractmethod
    def fetch_unread_emails(self, limit=10) -> list[dict]:
        """Return list of {id, subject, from, snippet}"""
        pass
