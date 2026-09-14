# SOFA — Safe One For All

Local AI chatbox for everything, you need to create image, create music, chat or do anything safely when talking to AI? You don't need to search thousands of websites to find the best AI versions, SOFA has you covered; you can do everything with this AI and it's fully local so no cloud saving will happen.

## What is it?

SOFA is a fully local-first, privacy-focused, multi-purpose AI assistant application. It brings together tools like chat, image generation, watermark removal, and a music/voice sketch generator in a single sidebar-navigated interface; your content is never logged to disk or to any cloud by default.

## LLM Backend

SOFA doesn't require you to sign up for and manage separate API keys for every free provider. Instead, it talks to locally running **OpenAI-compatible gateways**:

- **[OmniRoute](https://github.com/diegosouzapw/OmniRoute)** — zero-config, gives access to 290+ providers with no key required after install. Default endpoint: `http://localhost:20128/v1`
- **[FreeLLMAPI](https://github.com/tashfeenahmed/freellmapi)** — combines 34+ free LLM providers behind a single `/v1` endpoint. Default endpoint: `http://localhost:3001/v1`

Which one is used is selected via `CHAT_PROVIDER` (`omniroute` or `freellmapi`) in the `.env` file; since both services use OpenAI's `/chat/completions` and `/images/generations` format, SOFA's backend can talk to either one through a single generic client.

## Folder Structure

```
SOFA-Safe-One-For-All-/
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # centralized .env-based settings
│   ├── utils/
│   │   └── logger.py            # privacy-first logger
│   └── modules/
│       ├── chat/                # Chat & Assistant module
│       │   ├── schemas.py
│       │   ├── service.py       # OmniRoute / FreeLLMAPI client
│       │   └── router.py
│       ├── media/                # Media generation & processing module
│       │   ├── schemas.py
│       │   ├── service.py       # image generation + watermark removal template
│       │   └── router.py
│       ├── music/                # Music Creator module (draft/template)
│       │   ├── schemas.py
│       │   ├── service.py       # TTS-based placeholder for real music generation
│       │   └── router.py
│       └── privacy/              # Secure local tools module
│           ├── schemas.py
│           ├── service.py       # temp-file wiping, status report
│           └── router.py
├── static/
│   ├── css/style.css
│   ├── js/splash.js              # intro animation controller
│   └── js/app.js                 # sidebar switching + API integration
├── templates/
│   └── index.html                 # splash screen + sidebar app shell
├── start_sofa.bat                 # Windows launcher (visible console, for debugging)
├── sofa_silent.bat                 # Windows launcher used by SOFA.vbs (no console)
├── SOFA.vbs                        # double-click this (or a shortcut to it) to launch silently
└── stop_sofa.bat                   # stops the server started by SOFA.vbs
```

## Setup

1. **Install an LLM gateway** (at least one):
   ```bash
   # OmniRoute (recommended, zero-config)
   npm install -g omniroute
   omniroute

   # or FreeLLMAPI
   curl -fsSL https://freellmapi.co/install.sh | bash
   ```

2. **Install Python dependencies:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit CHAT_PROVIDER, base URLs and keys if needed.
   ```

4. **Run the app:**
   ```bash
   uvicorn app.main:app --reload
   ```
   Open `http://127.0.0.1:8000` in your browser.

   **On Windows**, you can instead double-click **`SOFA.vbs`** (or a desktop
   shortcut pointing to it) to launch SOFA with no visible console window —
   it sets up the venv/dependencies on first run and opens your browser
   automatically. Use **`stop_sofa.bat`** to stop it, or `start_sofa.bat`
   (visible console) if you need to see error output while troubleshooting.

## Privacy

- With `SOFA_NO_LOG=true` (default), no chat/media content is ever written to disk or the console.
- All local temp files can be wiped with a single click from the "Privacy" tab.
- No data is ever sent anywhere except the local gateway you explicitly configured.
