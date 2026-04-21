import os
import re
import base64
import logging
from email.utils import parsedate_to_datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .base_mail_service import BaseMailService

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
BODY_LIMIT = 3000  # chars sent to Ollama per email
URL_PATTERN = re.compile(r'https?://[^\s<>"\']+')
MAX_LINKS = 3


class GmailService(BaseMailService):
    def __init__(self, credentials_file="credentials.json", token_file="gmail_token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None

    def authenticate(self):
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0, open_browser=False)
            with open(self.token_file, "w") as f:
                f.write(creds.to_json())

        self.service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail authenticated")

    def fetch_unread_emails(self, limit=10) -> list[dict]:
        if not self.service:
            self.authenticate()

        try:
            results = self.service.users().messages().list(
                userId="me", q="is:unread in:inbox", maxResults=limit
            ).execute()
        except Exception as e:
            logger.error(f"Gmail list error: {e}")
            return []

        messages = results.get("messages", [])
        emails = []
        for msg in messages:
            details = self._get_email_details(msg["id"])
            if details:
                emails.append(details)
        return emails

    def _get_email_details(self, message_id) -> dict | None:
        try:
            msg = self.service.users().messages().get(
                userId="me",
                id=message_id,
                format="full",
            ).execute()

            headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
            body = self._extract_body(msg["payload"])
            links = list(dict.fromkeys(URL_PATTERN.findall(body)))[:MAX_LINKS]

            date_str = headers.get("Date", "")
            try:
                date = parsedate_to_datetime(date_str).strftime("%d/%m/%Y %H:%M") if date_str else ""
            except Exception:
                date = date_str

            return {
                "id": message_id,
                "subject": headers.get("Subject", "(no subject)"),
                "from": headers.get("From", "Unknown"),
                "date": date,
                "snippet": body[:BODY_LIMIT] if body else msg.get("snippet", ""),
                "links": links,
                "labels": msg.get("labelIds", []),
            }
        except Exception as e:
            logger.error(f"Gmail get message error {message_id}: {e}")
            return None

    def _extract_body(self, payload) -> str:
        """Recursively extract plain text body from email payload."""
        if payload.get("mimeType") == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        for part in payload.get("parts", []):
            result = self._extract_body(part)
            if result:
                return result

        return ""
