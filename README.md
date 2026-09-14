# SOFA — Safe One For All

Local AI chatbox for everything, you need to create image, create music, chat or do anything safely when talking to AI? You don't need to search thousands of websites to find the best AI versions, SOFA has you covered; you can do everything with this AI and it's fully local so no cloud saving will happen.

## What is it?

SOFA is a fully local-first, privacy-focused, multi-purpose AI assistant application. It brings together tools like chat, image generation, watermark removal, and a music/voice sketch generator in a single sidebar-navigated interface; your content is never logged to disk or to any cloud by default.

## LLM Backend

SOFA doesn't require you to sign up for and manage separate API keys for every free provider. Instead, it talks to locally running **OpenAI-compatible gateways**:

- **[OmniRoute](https://github.com/diegosouzapw/OmniRoute)** — zero-config, gives access to 290+ providers with no key required after install. Default endpoint: `http://localhost:20128/v1`
- **[FreeLLMAPI](https://github.com/tashfeenahmed/freellmapi)** — combines 34+ free LLM providers behind a single `/v1` endpoint. Default endpoint: `http://localhost:3001/v1`

Since both services use OpenAI's `/chat/completions`, `/images/generations` and `/audio/speech` format, SOFA's backend can talk to either one through a single generic client — and it goes further: each module (Chat, Image Creation, Music Creator) tries an **ordered fallback chain** of providers. If the first one fails (network error, HTTP error, missing key), it automatically retries the next one — no user-visible interruption. The order is configurable per module via `CHAT_PROVIDER_ORDER`, `MEDIA_PROVIDER_ORDER`, and `MUSIC_PROVIDER_ORDER` in `.env` (comma-separated, e.g. `freellmapi,omniroute`).

Music Creator additionally supports **[SunoAPI.org](https://sunoapi.org)** as a first-class provider for real music generation (set `SUNOAPI_API_KEY`) — when configured, it's tried before falling back to the TTS-based placeholder on the gateway chain.

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
│   │   ├── logger.py            # privacy-first logger
│   │   └── gateway.py           # shared fallback-chain resolution (OmniRoute/FreeLLMAPI)
│   └── modules/
│       ├── chat/                # Chat & Assistant module
│       │   ├── schemas.py
│       │   ├── service.py       # fallback chain across gateways
│       │   └── router.py
│       ├── media/                # Media generation & processing module
│       │   ├── schemas.py
│       │   ├── service.py       # image generation (fallback chain) + watermark removal template
│       │   └── router.py
│       ├── music/                # Music Creator module
│       │   ├── schemas.py
│       │   ├── service.py       # SunoAPI.org (real music) + TTS fallback chain
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
├── SOFA.ico                         # app/shortcut icon
├── installer/
│   └── SOFA_Setup.nsi               # NSIS source for the Windows SOFA-Setup.exe installer (the installer)
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
   # Edit the *_PROVIDER_ORDER fallback chains, base URLs and keys if needed.
   ```

4. **Run the app:**
   ```bash
   uvicorn app.main:app --reload
   ```
   Open `http://127.0.0.1:8000` in your browser.

   **On Windows**, use **`SOFA-Setup.exe`** instead (download it from the
   [Releases](../../releases) page, or build it yourself — see below) —
   the official installer: a real wizard that sets up the venv, installs
   dependencies, creates `.env`, best-effort installs OmniRoute if `npm`
   is available, and adds a **"SOFA AI"** Desktop + Start Menu shortcut
   with the SOFA icon.

   **Uninstalling**: the installer also drops an `Uninstall.exe` inside
   the install folder, so if you decide you don't want it, you can remove
   everything three ways — double-click `Uninstall.exe` directly, use the
   "Kaldır" (Uninstall) shortcut it adds to the SOFA Start Menu folder, or
   remove it like any other app from Windows Settings → Apps.

   Either way, launching SOFA afterwards (via the shortcut or `SOFA.vbs`)
   starts it with no visible console window and starts OmniRoute in the
   background automatically if it's installed. Use **`stop_sofa.bat`** to
   stop both, or `start_sofa.bat` (visible console) if you need to see
   error output while troubleshooting.

### Building the Windows installer

`SOFA-Setup.exe` isn't committed to the repo (it's a build artifact, gitignored) —
grab a prebuilt copy from [Releases](../../releases), or build it yourself with
[NSIS](https://nsis.sourceforge.io/) (`sudo apt install nsis` on Linux/WSL, or
the Windows installer from the NSIS site):

```bash
makensis installer/SOFA_Setup.nsi
```

This produces `installer/SOFA-Setup.exe`.

## Before you can actually use it

SOFA itself is "bring your own free API key" by design — no key is bundled,
for privacy and security reasons. **A fresh install has nothing to talk to
until you do this once:**

1. Install and run **OmniRoute** or **FreeLLMAPI** (step 1 above) — this is
   a separate local app/process; `SOFA-Setup.exe` only auto-installs
   OmniRoute for you if `npm` is already on your system.
2. On that gateway's own dashboard, connect at least one free provider key
   for **chat** (e.g. Groq, Gemini) and, if you want Image Creation to work,
   one that does image generation (e.g. Stability). None of this happens
   inside SOFA — it's configured entirely within OmniRoute's/FreeLLMAPI's
   own panel.
3. For real Music Creator output, get a free key from
   [SunoAPI.org](https://sunoapi.org) and set `SUNOAPI_API_KEY` in `.env`.
4. **Restart SOFA after editing `.env`** — settings are only read at startup,
   so a running instance won't pick up a key you just added.

Without step 2, Chat/Image Creation/Music Creator will return a "could not
reach provider" error instead of a reply — this isn't a bug, it just means
no gateway/key is reachable yet.

## Privacy

- With `SOFA_NO_LOG=true` (default), no chat/media content is ever written to disk or the console.
- All local temp files can be wiped with a single click from the "Privacy" tab.
- No data is ever sent anywhere except the local gateway you explicitly configured.
