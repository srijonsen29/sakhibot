import base64
from groq import Groq, APIStatusError, RateLimitError
from config import GROQ_API_KEY, VISION_MODEL

_client = Groq(api_key=GROQ_API_KEY)

VISION_SYSTEM_PROMPT = (
    "You are helping analyze an image submitted by someone seeking legal or "
    "safety help in India through a women's rights assistant. The image may "
    "be a screenshot of abusive messages, a photo of a document (FIR, ID, "
    "notice, letter), or a photo related to an incident they want to report.\n\n"
    "Rules:\n"
    "1. If the image contains text (a chat screenshot, document, letter), "
    "transcribe the important text as accurately as you can.\n"
    "2. If it is a photo rather than text, give a brief, factual, neutral "
    "description of what is visibly there. Do not diagnose injuries, guess "
    "medical severity, or speculate about anything not clearly visible.\n"
    "3. Never invent details that are not visible in the image.\n"
    "4. Keep your answer under 200 words, calm and factual, plain text only "
    "(no markdown headers or asterisks).\n"
    "5. If the image is unrelated to a legal/safety context (e.g. a random "
    "photo), just describe it briefly and factually anyway."
)


def analyze_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """
    Sends an image to Groq's vision model and returns a plain-text
    description/transcription that can be fed into the normal chat pipeline
    (translation -> emergency detection -> orchestrator) as extra context.

    Returns "" if the vision call fails for any reason — callers should
    treat an empty string as "could not read the image" and fall back
    gracefully rather than raising.
    """
    try:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64}"

        response = _client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {"role": "system", "content": VISION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please describe or transcribe this image.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url},
                        },
                    ],
                },
            ],
            temperature=0.2,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()

    except RateLimitError as e:
        print(f"  [VISION] Rate limited: {e}")
        return ""
    except APIStatusError as e:
        print(f"  [VISION] Groq API error: {e}")
        return ""
    except Exception as e:
        print(f"  [VISION] Unexpected error: {e}")
        return ""
