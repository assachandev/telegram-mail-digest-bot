"""
Run this script ONCE on your local machine (requires a browser) to generate gmail_token.json.
Then copy the token file to your server.

Usage:
    pip install google-auth-oauthlib
    python auth.py
"""
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
credentials_file = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
token_file = os.getenv("GMAIL_TOKEN_FILE", "gmail_token.json")

flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
creds = flow.run_local_server(port=0)

with open(token_file, "w") as f:
    f.write(creds.to_json())

print(f"✅ Token saved to: {token_file}")
print(f"   Copy this file to your server's data directory.")
