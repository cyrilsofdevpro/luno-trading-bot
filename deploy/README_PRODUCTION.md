# Production deployment notes — Luno trading bot

This file lists recommended, copy-paste ready steps to deploy the bot to a Linux VPS (Ubuntu) using `gunicorn` + `systemd` and `nginx` as a reverse proxy with TLS via Let's Encrypt.

Prerequisites
- A VPS (Ubuntu 22.04+ recommended) with a public domain name pointed to it.
- SSH access and sudo privileges.
- The project files placed under `/opt/luno-bot` (or adjust the paths below).

Quick setup (Ubuntu)

1. Prepare system

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx certbot python3-certbot-nginx git
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
```

2. Deploy project

```bash
sudo mkdir -p /opt/luno-bot
sudo chown $USER:$USER /opt/luno-bot
cd /opt/luno-bot
# copy repo files here (git clone or rsync)
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r '/path/to/Luno trading  Bot/requirements.txt'
```

3. Configure environment

Create a `.env` file in the project root with your secrets (do NOT commit this file):

```
LUNO_API_KEY=your_key_here
LUNO_API_SECRET=your_secret_here
TRADING_PAIR=XBTNGN
DRY_RUN=true
TV_WEBHOOK_TOKEN=some_random_secret
```

4. Install systemd unit

Copy `deploy/luno-bot.service` to `/etc/systemd/system/luno-bot.service` and edit the `User`, `WorkingDirectory`, and `Environment` lines to match your install. Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now luno-bot
sudo journalctl -u luno-bot -f
```

5. Configure nginx and TLS

Copy `deploy/nginx/luno-bot.conf` to `/etc/nginx/sites-available/luno-bot`, replace `server_name` with your domain, and enable it:

```bash
sudo ln -s /etc/nginx/sites-available/luno-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d your.domain.example
```

6. Health checks and monitoring

- The app exposes `/healthz` which returns HTTP 200 when the process is healthy. Use an external monitoring service to poll it.
- Logs: `deploy` created nginx logs; configure application logs to `/var/log/luno-bot` and add `logrotate` rules.

Windows notes
- Use `waitress` or `gunicorn` windows alternatives, and wrap startup in NSSM to create a Windows service.
- Use Cloudflare or a reverse proxy to obtain TLS if you don't want to manage certs locally.

Security notes
- Keep `TV_WEBHOOK_TOKEN` secret and use it in TradingView webhook URL as a query param or in the body.
- Prefer `dry_run=true` for first tests. Only set `DRY_RUN=false` after you're confident.

Testing after deployment

1. From a machine with access to the public URL (or via ngrok), send a dry-run webhook:

```powershell
$payload = @{ signal='buy'; pair='ETH'; volume=0.001; dry_run=$true }
Invoke-RestMethod -Uri 'https://your.domain.example/tv-webhook?token=YOUR_TOKEN' -Method POST -Body ($payload | ConvertTo-Json -Depth 6) -ContentType 'application/json'
Invoke-RestMethod -Uri 'https://your.domain.example/tv-webhook/status' -Method GET | ConvertTo-Json -Depth 6
```

2. Confirm the dashboard shows `/api/tradingview/status` with `active: true` and a `last_seen` timestamp.

3. When ready, set `DRY_RUN=false` and start with minimal order sizes.

If you want, I can also:
- Add a `logrotate` config and a basic monitoring `healthcheck` script.
- Create a Windows service wrapper script and example NSSM instructions.
# Production deployment guide — Luno trading bot

This document contains copy-paste instructions to deploy the bot on a Linux VPS (Ubuntu) behind Nginx with Gunicorn and TLS (Let's Encrypt).

Prerequisites
- Ubuntu 20.04+ (or similar Linux)
- root or sudo access
- A domain name pointing to the server (A record)

1) Copy project to server

Place the repository under `/opt/luno-bot` and make sure the files (including `dashboard.py`, `requirements.txt`, and `.env`) are present.

2) Create Python virtualenv and install dependencies

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx certbot python3-certbot-nginx
sudo mkdir -p /opt/luno-bot
sudo chown $USER:$USER /opt/luno-bot
cd /opt/luno-bot
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r /path/to/requirements.txt
```

3) Configure environment

Create `/opt/luno-bot/.env` and add:

```
LUNO_API_KEY=your_key_here
LUNO_API_SECRET=your_secret_here
TRADING_PAIR=XBTNGN
DRY_RUN=true
TV_WEBHOOK_TOKEN=choose_a_secure_token
```

Adjust owner and permissions so the `www-data` user (or the service user you choose) can read the file.

4) systemd service (Gunicorn)

Copy `deploy/systemd/luno-bot.service` to `/etc/systemd/system/luno-bot.service` and edit `User`, `Group`, `WorkingDirectory`, and `Environment` (or set secrets in a safer store). Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now luno-bot
sudo journalctl -u luno-bot -f
```

5) Nginx

Use the provided `deploy/nginx/luno-bot.conf` as a template. Update `server_name` to your domain. Then enable and test:

```bash
sudo ln -s /opt/luno-bot/deploy/nginx/luno-bot.conf /etc/nginx/sites-available/luno-bot
sudo ln -s /etc/nginx/sites-available/luno-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

6) TLS via Certbot

```bash
sudo certbot --nginx -d your.domain.example
```

7) Healthcheck and monitoring

- The app exposes `/healthz` which should return 200. Configure your uptime monitor to poll it.
- Logs are visible via `journalctl -u luno-bot` and your app's log file (configurable via `BOT_LOG_FILE` env var).

8) Testing (dry run)

Send a safe dry-run TradingView-like POST:

```bash
curl -s -X POST "https://your.domain.example/tv-webhook?token=choose_a_secure_token" \
  -H 'Content-Type: application/json' \
  -d '{"signal":"buy","pair":"ETH","volume":0.001,"dry_run":true}'

# Check status
curl -s https://your.domain.example/api/tradingview/status | jq .
```

9) Going live

When you're confident, set `DRY_RUN=false` in `.env` and restart the service. Start with very small order sizes to validate behavior.

Security notes
- Keep API keys and tokens out of the repo. Use env vars or a secrets manager.
- Only accept HTTPS traffic through the reverse proxy.
- Rotate keys regularly and use alerts for failure conditions.
Production deployment checklist

1) Copy project to VPS, create virtualenv, install requirements.

2) Create an environment with the following variables (systemd unit or env file):
   - LUNO_API_KEY
   - LUNO_API_SECRET
   - TV_WEBHOOK_TOKEN  # required for webhook authentication

3) Use the provided systemd unit (`deploy/systemd/luno-bot.service`) as a template.
   - Update WorkingDirectory and ExecStart to match your installation path.

4) Configure nginx using `deploy/nginx/luno-bot.conf`, enable site, and obtain TLS cert via certbot.

5) Start and enable service:
   sudo systemctl daemon-reload
   sudo systemctl enable --now luno-bot
   sudo journalctl -u luno-bot -f

6) Test health and webhook (dry-run):
   curl -X GET https://your.domain.example/healthz
   curl -X POST https://your.domain.example/tv-webhook?token=YOUR_TOKEN -H 'Content-Type: application/json' -d '{"signal":"buy","pair":"ETH","volume":0.001,"dry_run":true}'

Security notes:
- Keep LUNO_API_KEY/SECRET secret and rotate regularly.
- Use HTTPS (Let's Encrypt) and firewall rules.
- Monitor logs and set alerts for failed orders or unexpected errors.
