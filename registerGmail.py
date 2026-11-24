import os
import glob
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes needed: modify allows reading emails, sending replies, marking read/unread, etc.
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

TOPIC_NAME = "projects/co-in-pacey-app/topics/test_langgraph_agent"
TOKEN_FILE = "token.json"


def get_gmail_service():
    """Authenticates the user and returns an authorized Gmail API service."""
    creds = None

    # 1. Load cached token if it exists
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # 2. If no valid credentials, perform OAuth login or refresh token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired access token...")
            creds.refresh(Request())
        else:
            # Find client_secret JSON file in the directory
            secret_files = glob.glob("client_secret*.json")
            if not secret_files:
                raise FileNotFoundError("Could not find client_secret JSON file in this directory.")
            client_secret_file = secret_files[0]
            print(f"Using credentials file: {client_secret_file}")

            # Open browser for user login & consent
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
            creds = flow.run_local_server(port=0)

        # 3. Cache the token for future runs
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
            print(f"Credentials saved to {TOKEN_FILE}")

    return build("gmail", "v1", credentials=creds)


def register_gmail_watch(gmail_service):
    """Registers Gmail push notifications to the GCP Pub/Sub topic."""
    request = {
        "topicName": TOPIC_NAME,
        "labelIds": ["INBOX"],
        "labelFilterBehavior": "INCLUDE",
    }

    response = (
        gmail_service.users()
        .watch(userId="me", body=request)
        .execute()
    )

    print("\n✅ Watch registered successfully!")
    history_id = response.get("historyId")
    print("History ID:", history_id)
    print("Expiration (timestamp ms):", response.get("expiration"))

    # Save initial history ID as baseline for the webhook
    if history_id:
        with open("last_history_id.txt", "w") as f:
            f.write(str(history_id))
        print("Saved baseline history ID to last_history_id.txt")

    return response


if __name__ == "__main__":
    print("1. Authenticating with Gmail...")
    service = get_gmail_service()

    print("\n2. Registering watch on Gmail Inbox...")
    register_gmail_watch(service)
