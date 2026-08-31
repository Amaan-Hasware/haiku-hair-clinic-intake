# GenoRoot Hair & Scalp Clinic — AI Intake Form

A conversational AI intake assistant for GenoRoot Hair & Scalp Clinic, built as a take-home assignment for Haiku Studio. Replaces a traditional paper intake form with a warm, natural chat experience that collects 16 patient fields before a hair health consultation.

---

## What It Does

- Greets the patient and collects 16 clinical fields through natural conversation (not a form dump)
- Shows a live progress bar (X / 16 fields filled) as answers are detected
- Locks the chat and reveals a **Proceed** button once all 16 fields are collected
- On confirmation, saves the completed intake as `intake_result.json`
- If any fields are missing at submission, Gemini is automatically prompted to re-ask only those fields

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend | Flask (Python) | Lightweight, minimal boilerplate for a single-purpose API |
| LLM | Gemini via `google-genai` SDK | Free tier available; strong instruction-following for structured output |
| Field extraction | `[FIELDS]...[/FIELDS]` JSON block in every Gemini reply | Single LLM call returns both conversational text and structured state — no second call needed |
| Session memory | In-memory Python dict + list | Simple enough for a single-session intake; no DB overhead |
| Frontend | Vanilla HTML / CSS / JS | No framework needed; keeps the bundle zero-dependency |

---

## Project Structure

```
haiku-hair-clinic-intake/
├── app.py                  # Flask app — routes, Gemini call, field extraction
├── prompts.py              # System prompt with field list and output rules
├── requirements.txt        # Python dependencies
├── .env                    # API key (never committed — see .gitignore)
├── .gitignore
├── templates/
│   └── index.html          # Chat UI with progress bar and completion overlay
├── static/
│   ├── style.css           # GenoRoot brand styles + dark mode
│   └── app.js              # Fetch calls, typing indicator, progress updates
└── tests/
    ├── test_structural.py  # TC1 — Gemini always returns valid [FIELDS] JSON
    └── test_submit_guard.py # TC2 — /submit rejects incomplete, saves when full
```

---

## Setup & Installation

### Prerequisites

- Python 3.9+
- A Google Gemini API key → [Get one free at Google AI Studio](https://aistudio.google.com/app/apikey)

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/Amaan-Hasware/haiku-hair-clinic-intake.git
cd haiku-hair-clinic-intake
```

---

### Step 2 — Create a virtual environment

**Standard Python (recommended path):**

```bash
python -m venv venv
```

> **If you have Anaconda installed and the above fails** with an `ensurepip` error like:
> `Error: Command '['...\venv\Scripts\python.exe', '-Im', 'ensurepip', '--upgrade']' returned non-zero exit status 1`
>
> Anaconda's Python sometimes blocks `ensurepip`. Use this two-step workaround instead:
>
> ```bash
> python -m venv venv --without-pip
> ```
> Then manually bootstrap pip into the venv:
> ```bash
> .\venv\Scripts\python.exe -m ensurepip
> ```

---

### Step 3 — Activate the virtual environment

```bash
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (Command Prompt)
.\venv\Scripts\activate.bat

# macOS / Linux
source venv/bin/activate
```

You should see `(venv)` appear at the start of your terminal prompt.

---

### Step 4 — Install dependencies

**Standard path:**

```bash
pip install -r requirements.txt
```

> **If you have Anaconda installed and packages end up in Anaconda instead of the venv:**
> This happens when `pip` resolves to Anaconda's pip rather than the venv's. Use the venv's Python directly:
>
> ```bash
> .\venv\Scripts\python.exe -m pip install -r requirements.txt
> ```
>
> You can verify packages are installed in the right place with:
> ```bash
> .\venv\Scripts\python.exe -m pip list
> ```

---

### Step 5 — Add your API key

Create a `.env` file in the project root (same folder as `app.py`):

```
GOOGLE_API_KEY=your_api_key_here
```

This file is in `.gitignore` — it will never be committed to GitHub.

---

### Step 6 — Run the app

```bash
python app.py
```

> **Anaconda users** — if you get a `ModuleNotFoundError` even after installing:
>
> ```bash
> .\venv\Scripts\python.exe app.py
> ```

Open your browser at **http://127.0.0.1:5000**

---

## Running Tests

```bash
# Standard path (venv activated)
python -m pytest tests/

# Anaconda users — always prefix with venv Python to avoid the global interpreter
.\venv\Scripts\python.exe -m pytest tests/
```

### Test Coverage

| Test File | ID | What it checks |
|---|---|---|
| `test_structural.py` | TC1a | `[FIELDS]` block is present in every Gemini reply |
| `test_structural.py` | TC1b | Content between `[FIELDS]` tags is valid JSON |
| `test_structural.py` | TC1c | All 16 required keys are present in the JSON |
| `test_submit_guard.py` | TC2a | `/submit` returns `status=incomplete` when fields have `None` values |
| `test_submit_guard.py` | TC2b | `/submit` returns the exact names of missing fields |
| `test_submit_guard.py` | TC2c | `/submit` saves `intake_result.json` when all 16 fields are filled |

---

## Architectural Decisions

### Why not LangChain?

LangChain is useful when you need chains of LLM calls, retrieval, agents, or tool use. This project makes exactly one Gemini call per user turn. Adding LangChain would have introduced ~10 abstraction layers over a `client.models.generate_content()` call. Kept it direct.

### Why not ConversationSummaryMemory?

The intake is a bounded 16-question conversation — the full transcript fits comfortably in a single Gemini context window. Summary memory is worth it when histories grow long enough to exceed the context limit. Not needed here.

### Why a `[FIELDS]` JSON block instead of two LLM calls?

The simpler approach would be one call for the conversational reply and a second call to extract structured data. One call is cheaper, faster, and avoids the two responses going out of sync. The system prompt instructs Gemini to always append a `[FIELDS]...[/FIELDS]` block; the backend splits on that tag to get both pieces from a single response.

### Why a key-filter on field extraction?

```python
filled_fields.update({k: v for k, v in extracted.items() if v is not None and k in filled_fields})
```

Gemini occasionally returns slightly misspelled keys (e.g. `age_hair_loss_begin` vs `age_hair_loss_began`). Without the `k in filled_fields` guard, those hallucinated keys would be silently added to the dict, causing the progress count to exceed 16. The guard ignores any key that wasn't declared upfront.

### Why not embedding-based off-topic detection?

We considered checking semantic similarity between each user message and "hair health" to detect off-topic input. Rejected: it requires a vector model, adds latency, and the accuracy gain over a well-worded system prompt instruction is marginal for this use case. The guardrail lives in the system prompt instead. With more time, embedding-based relevance scoring would be worth adding for robustness.

### Why write `intake_result.json` only at the end?

Incremental writes after each field would require file-locking logic and produce a partially-filled file if the user abandons mid-session. Writing once at submission keeps the output atomic — the file either has all 16 fields or it doesn't exist.

### Why `google-genai` and not `google-generativeai`?

`google-generativeai` is deprecated. The new `google-genai` SDK requires `types.Content` / `types.Part` objects (not raw dicts) for conversation history. All Gemini calls in this project use the new SDK format.

---

## What Would Be Improved With One More Week

1. **Embedding-based off-topic guard** — Replace the system-prompt guardrail with cosine similarity scoring against a "hair health" anchor embedding for more robust filtering.

2. **Streaming responses** — Gemini supports streaming (`generate_content_stream`), which would make replies appear word-by-word like ChatGPT instead of all at once. However, this would require moving away from Flask to an async framework like FastAPI, since Flask's synchronous request-response model isn't well suited for streaming. It would be a meaningful architectural change, not just a drop-in swap.

3. **Production deployment** — The app currently runs on Flask's built-in dev server, which is single-threaded and not meant for real users. If this were to move to a production stage, it would need a much more robust setup: a proper WSGI server like Gunicorn, a reverse proxy (Nginx), HTTPS, and the API key managed via a secrets manager rather than a `.env` file.

4. **Retry with exponential backoff** — The current error handler catches 429s and returns a user-friendly message. A proper implementation would retry automatically with jitter before surfacing the error.

5. **Female-specific field handling** — Fields `menstrual_cycle` and `pregnancy_related` are marked "female only" in the system prompt but the backend treats them the same as all other fields. A smarter implementation would skip them (and reduce the required count to 14) when the patient indicates they are male.

---

## Environment Variables

| Variable | Description |
|---|---|
| `GOOGLE_API_KEY` | Your Gemini API key from Google AI Studio |

---

## .gitignore (important files excluded from version control)

```
.env                  # API key — never commit this
intake_result.json    # Patient data — never commit this
venv/                 # Virtual environment
__pycache__/
```
