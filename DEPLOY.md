# Deploy — public endpoint for the Agent Games Wildcard form

The guard is verified live against BSC, but the form needs a **public HTTPS
URL**. This repo is now deploy-ready: `server.py` reads the host-assigned
`$PORT` (Render/Railway assign one; local default is still 8080), and
`render.yaml` / `Procfile` / `Dockerfile` are included. Pure stdlib, no
dependencies, no secrets, no keys.

## Option A — Render (free, recommended, ~10 min)

1. Push this folder to GitHub (`riniprinces/bsc-wallet-guard`).
2. Open https://dashboard.render.com → **New +** → **Web Service** →
   connect the `bsc-wallet-guard` repo. Render picks up `render.yaml`
   automatically (Free plan, build `pip install -r requirements.txt`,
   start `python3 server.py`).
3. Wait for deploy → copy the URL, e.g.
   `https://bsc-wallet-guard.onrender.com`.
4. Test it:
   ```bash
   curl https://bsc-wallet-guard.onrender.com/health
   curl -X POST https://bsc-wallet-guard.onrender.com/guard \
     -H 'Content-Type: application/json' \
     -d '{"spender":"0x10ED43C718714eb63d5aA57B78B54704E256024E","token":"0x55d398326f99059fF775485246999027B3197955","amount":"1000000000000000000"}'
   # expect {"verdict": "SAFE", ... "token_symbol": "USDT"}
   ```
5. **Keep it warm (important):** Render's free tier sleeps after ~15 min
   idle and takes ~30–60 s to wake. Add a free UptimeRobot monitor
   (5-min interval) on `<url>/health` so the judges' first `/guard` call
   doesn't hit a cold start.
6. Paste the public URL + repo link into the Agent Games Wildcard form
   (submit with your own X login).

## Option B — Railway (free trial credit)

New Project → Deploy from GitHub → pick the repo. Railway sets `$PORT`
itself; start command is `python3 server.py` (see `Procfile`). Same
curl test as above, same keep-warm note.

## Fallback — tunnel from your own PC

If free hosting is slow to approve, run `python3 server.py` on your PC
and expose it with `ngrok http 8080` (or Cloudflare Tunnel) — that gives
a public URL in a minute. The VM's tunnels were all blocked, so this one
has to run from your PC, not from here.

## What NOT to do

- Don't hardcode a port: hosts assign `$PORT` and the app must listen on
  it (fixed in `server.py`).
- Don't leave the URL untested: hit `/health` and the PancakeSwap/USDT
  `/guard` example above before pasting it into the form.
