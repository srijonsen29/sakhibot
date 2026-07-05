# SakhiBot — Image Upload Feature + Model Fixes

Drop these files into your local `sakhibot` clone at the matching paths
(they overwrite the originals), then:

```bash
git add .
git commit -m "Add image upload/analysis feature, fix deprecated Groq models"
git push
```

## What's new

### 1. Image upload feature (new)
- **`backend/vision.py`** (new file) — sends an uploaded image to Groq's
  vision model and returns a plain-text description/transcription.
- **`backend/main.py`** — refactored the `/api/chat` logic into a shared
  `process_chat_message()` helper, and added a new endpoint:
  **`POST /api/chat/image`** (multipart form: `image`, `message`,
  `language`, `history`, `district`, `state_name`). It runs the image
  through the vision model, then feeds the result through your *existing*
  translate → emergency-detect → LangGraph pipeline, so nothing about your
  legal/safety logic had to change.
- **`frontend/src/components/ImageButton.jsx`** (new) — attach button,
  matches your `VoiceButton` style, validates file type/size client-side.
- **`frontend/src/components/InputBar.jsx`** — wires in the image button +
  a small thumbnail preview with a remove (×) control.
- **`frontend/src/App.jsx`** — `handleSend` now takes an optional image and
  calls the new `sendImageMessage()` API function when one is attached.
- **`frontend/src/api.js`** — added `sendImageMessage()`.
- **`frontend/src/components/MessageBubble.jsx`** — shows the attached
  image thumbnail on the user's bubble, and an expandable "What I read
  from your image" note on the bot's reply, so users can double-check
  what the AI actually extracted (important since this could be evidence).

### 2. Voice — already done, untouched
`VoiceButton.jsx` (speech-to-text) and the `TTSButton` inside
`MessageBubble.jsx` (text-to-speech) already existed in your repo and work
fine — no changes needed there.

### 3. Model fixes (important, unrelated to image feature)
`backend/config.py` — your `LLM_MODELS` fallback chain was entirely
deprecated by Groq (`llama-3.1-8b-instant`, `llama-3.3-70b-versatile`,
`mixtral-8x7b-32768`). Replaced with Groq's current recommended models
(`openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `qwen/qwen3.6-27b`). **If your
deployed bot has been giving the generic "high demand" fallback message
lately, this was probably why** — worth checking your server logs.

## Notes / things to double check

- **Vision model is a preview model.** As of writing, `qwen/qwen3.6-27b` is
  the only vision-capable model Groq offers (Llama 4 Scout/Maverick, which
  used to do this, were deprecated). Groq marks it "preview" (not
  guaranteed stable). Check https://console.groq.com/docs/vision
  periodically — if Groq ships a new production vision model, just update
  `VISION_MODEL` in `config.py`.
- **8MB image size limit** is enforced both client-side (`ImageButton.jsx`)
  and server-side (`MAX_IMAGE_BYTES` in `main.py`) — change both together
  if you adjust it.
- **`python-multipart`** was added to `requirements.txt` — required by
  FastAPI for `File`/`Form` uploads. Run `pip install -r requirements.txt`
  again after pulling.
- The vision system prompt in `vision.py` is deliberately conservative: it
  transcribes text and describes photos factually, but is instructed not
  to diagnose injuries or guess severity — worth a read/tweak given the
  domestic-violence context.
