Windows deployment notes — Luno trading bot

This file gives a minimal path to run the bot on Windows as a service and expose it securely.

1) Use Waitress to host Flask

Install in your venv:

venv\Scripts\activate
pip install -r requirements.txt
pip install waitress

Run with Waitress (for testing):

venv\Scripts\python -m waitress --port=8000 dashboard:app

2) Run as a Windows Service (NSSM)

- Download NSSM and install it.
- Create a new service with the NSSM GUI or CLI. Example (run as admin):

nssm install luno-bot "C:\path\to\venv\Scripts\python.exe" "C:\path\to\dashboard.py"
nssm set luno-bot AppDirectory C:\path\to\project
nssm set luno-bot AppParameters "-m waitress --port=8000 dashboard:app"
nssm set luno-bot AppEnvironmentExtra "LUNO_API_KEY=...;LUNO_API_SECRET=...;TV_WEBHOOK_TOKEN=..."
nssm start luno-bot

3) TLS & Public exposure

- Use Cloudflare (recommended) or add a reverse proxy (IIS or Nginx for Windows) to terminate TLS.
- Alternatively, use ngrok with a reserved domain for short-term public exposure.

4) Healthchecks

- Poll http://127.0.0.1:8000/healthz to verify the process is up. Configure your monitoring provider to check this.

5) Logging

- Configure BOT_LOG_FILE env var for log location. Make sure the service user has write permission.
