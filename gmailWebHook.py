import os
import base64
import json
from fastapi import FastAPI, Request
from googleapiclient.errors import HttpError
from registerGmail import get_gmail_service
from supportAgent import run_agent

app = FastAPI()

HISTORY_FILE = "last_history_id.txt"

# Lazy-loaded Gmail service instance
gmail_service = None


def get_service():
    global gmail_service
    if gmail_service is None:
        gmail_service = get_gmail_service()
    return gmail_service


def get_last_history_id() -> str | None:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            val = f.read().strip()
            if val.isdigit():
                return val
    return None


def save_last_history_id(history_id: str | int):
    with open(HISTORY_FILE, "w") as f:
        f.write(str(history_id))


def extract_email_body(payload: dict) -> str:
    """Recursively extracts plain text body (or html as fallback) from message payload."""
    plain_parts = []
    html_parts = []

    def _walk(part):
        mime_type = part.get("mimeType", "")
        data = part.get("body", {}).get("data")
        if data:
            try:
                # Add padding if needed for urlsafe_b64decode
                padded = data + "=" * (-len(data) % 4)
                decoded = base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
                if "text/plain" in mime_type:
                    plain_parts.append(decoded)
                elif "text/html" in mime_type:
                    html_parts.append(decoded)
            except Exception:
                pass

        for sub_part in part.get("parts", []):
            _walk(sub_part)

    _walk(payload)

    if plain_parts:
        return "\n".join(plain_parts).strip()
    elif html_parts:
        return "\n".join(html_parts).strip()
    return ""


# =====================================================================
# YOUR AI AGENT ENTRY POINT
# =====================================================================
def process_email_with_ai(email_data: dict):
    """
    Hook for your AI Support Agent.
    
    email_data contains:
      - id: str            (Gmail message ID)
      - thread_id: str     (Gmail thread ID)
      - from: str          (Sender name and email)
      - to: str            (Recipient email)
      - subject: str       (Email subject)
      - date: str          (Date sent)
      - snippet: str       (Short preview)
      - body: str          (Full email text)
      - labels: list       (e.g., ['INBOX', 'UNREAD'])
    """
    print("\n" + "=" * 60)
    print("🤖 DISPATCHING TO AI AGENT:")
    print(f"From:    {email_data['from']}")
    print(f"Subject: {email_data['subject']}")
    print(f"Snippet: {email_data['snippet']}")
    print(f"Body:\n{email_data['body'][:300]}...")  # print first 300 chars
    print("=" * 60 + "\n")
    run_agent(email_data)

    # >>> Put your LangGraph / LlamaIndex / Agent workflow code here <<<


# =====================================================================
# FASTAPI WEBHOOK ENDPOINT
# =====================================================================
@app.post("/gmail-webhook")
async def gmail_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON"}

    # Pub/Sub push messages have a 'message' field
    pubsub_message = payload.get("message")
    if not pubsub_message or "data" not in pubsub_message:
        return {"status": "ignored", "reason": "No Pub/Sub message data"}

    # 1. Decode notification
    try:
        data_bytes = base64.b64decode(pubsub_message["data"])
        notification = json.loads(data_bytes.decode("utf-8"))
    except Exception as e:
        print(f"Error decoding Pub/Sub payload: {e}")
        return {"status": "error", "message": "Failed to decode notification"}

    email_address = notification.get("emailAddress")
    new_history_id = str(notification.get("historyId", ""))

    print(f"\n📩 Notification received for {email_address} | New HistoryId: {new_history_id}")

    if not new_history_id:
        return {"status": "ignored", "reason": "Missing historyId"}

    # 2. Compare against last known historyId
    last_history_id = get_last_history_id()

    # If first time, set baseline history ID and return
    if not last_history_id:
        print(f"Setting baseline history ID: {new_history_id}")
        save_last_history_id(new_history_id)
        return {"status": "baseline_set", "historyId": new_history_id}

    if int(new_history_id) <= int(last_history_id):
        print("HistoryId already processed or older. Skipping.")
        return {"status": "already_processed"}

    service = get_service()

    # 3. Fetch history changes since last_history_id
    try:
        history_response = (
            service.users()
            .history()
            .list(
                userId="me",
                startHistoryId=last_history_id,
                historyTypes=["messageAdded"],
                labelId="INBOX",
            )
            .execute()
        )
    except HttpError as error:
        # History ID is too old or invalid (e.g., >30 days expired)
        if error.resp.status in (404, 400):
            print(f"Warning: History ID {last_history_id} expired. Resetting to {new_history_id}.")
            save_last_history_id(new_history_id)
            return {"status": "history_reset"}
        raise error

    history_records = history_response.get("history", [])
    processed_message_ids = set()

    # 4. Extract new messages & fetch full details
    for record in history_records:
        for msg_added in record.get("messagesAdded", []):
            msg = msg_added.get("message", {})
            msg_id = msg.get("id")

            if not msg_id or msg_id in processed_message_ids:
                continue

            processed_message_ids.add(msg_id)

            try:
                # Fetch full message details
                full_msg = (
                    service.users()
                    .messages()
                    .get(userId="me", id=msg_id, format="full")
                    .execute()
                )

                msg_payload = full_msg.get("payload", {})
                headers_list = msg_payload.get("headers", [])
                headers = {h["name"].lower(): h["value"] for h in headers_list}

                email_data = {
                    "id": msg_id,
                    "thread_id": full_msg.get("threadId"),
                    "from": headers.get("from", ""),
                    "to": headers.get("to", ""),
                    "subject": headers.get("subject", "(No Subject)"),
                    "date": headers.get("date", ""),
                    "snippet": full_msg.get("snippet", ""),
                    "labels": full_msg.get("labelIds", []),
                    "body": extract_email_body(msg_payload),
                }

                # 5. Dispatch to AI Agent
                process_email_with_ai(email_data)

            except Exception as e:
                print(f"Error fetching message {msg_id}: {e}")

    # 6. Update last_history_id
    save_last_history_id(new_history_id)

    return {"status": "success", "processed_count": len(processed_message_ids)}
