import os
import re
from twilio.rest import Client


def normalize_phone(number: str) -> str:
    """
    Normalize phone number to E.164 format.
    Handles Indian numbers stored without country code (e.g. 9836410469 → +919836410469).
    """
    # Strip spaces, dashes, brackets
    cleaned = re.sub(r"[\s\-\(\)]", "", number)

    # Already in E.164 format
    if cleaned.startswith("+"):
        return cleaned

    # Indian number starting with 0 (landline style)
    if cleaned.startswith("0"):
        cleaned = cleaned[1:]

    # 10-digit Indian mobile number → add +91
    if len(cleaned) == 10:
        return f"+91{cleaned}"

    # 12-digit starting with 91 → add +
    if len(cleaned) == 12 and cleaned.startswith("91"):
        return f"+{cleaned}"

    # Fallback — return as-is with + prefix
    return f"+{cleaned}"


def send_emergency_sms(to_number: str, message: str) -> bool:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    
    to_number = normalize_phone(to_number)

    if not account_sid or not auth_token or not from_number:
        # Mock mode fallback for local development
        print(f"\n[MOCK SMS SEND] To: {to_number}")
        print(f"[MOCK SMS CONTENT] {message}\n")
        return True

    try:
        client = Client(account_sid, auth_token)
        client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        return True
    except Exception as e:
        print(f"[SMS ERROR] Failed to send SMS to {to_number}: {e}")
        return False
