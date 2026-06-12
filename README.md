# TC Capital vs Martan Trading — Combined Site

One Streamlit website with all three apps:

| Page | What it shows |
|---|---|
| **Scoreboard** (front page) | Head-to-head competition: P&L, setups, win rates, charts |
| **TC Capital** | Capital, equity curve, per-instrument table, open positions, recent trades |
| **Martan Trading** | Same, for the upgraded system |

The site is **read-only** — trading control stays on the local dashboards
(port 8501/8502) and Telegram.

## Run locally

```
python -m streamlit run app.py --server.port 8504
```

Opens at http://localhost:8504 — it reads the live bot folders directly.
(Use the "Trading Website START.bat" shortcut on the Desktop.)

## Deploy free on Streamlit Community Cloud

The bots run on this PC, so the cloud site reads data from a private GitHub
repo that a scheduled task keeps up to date.

### One-time setup (~15 minutes)

1. **GitHub account** — create one at github.com if needed (free).

2. **Create two repos:**
   - `trading-data` — **private**. Holds the journals/portfolios.
   - `trading-site` — private or public. Holds the code in this folder.

3. **Push this folder** to `trading-site`:
   ```
   cd "C:\Users\Cloudius\OneDrive\Documents\TC_Martan_Site"
   git init && git add -A && git commit -m "initial site"
   git remote add origin https://github.com/<YOU>/trading-site.git
   git push -u origin main
   ```

4. **Clone the data repo and do the first sync:**
   ```
   git clone https://github.com/<YOU>/trading-data.git C:\Users\Cloudius\trading-data
   python "C:\Users\Cloudius\OneDrive\Documents\TC_Martan_Site\sync_data.py"
   ```

5. **Schedule the sync** (Task Scheduler → Create Basic Task → every 15 min):
   - Program: `python`
   - Arguments: `"C:\Users\Cloudius\OneDrive\Documents\TC_Martan_Site\sync_data.py"`

6. **Fine-grained GitHub token** (Settings → Developer settings → Fine-grained
   tokens): access to `trading-data` only, **Contents: Read-only**. Copy it.

7. **Deploy on [share.streamlit.io](https://share.streamlit.io)** (sign in with
   GitHub): New app → repo `trading-site`, branch `main`, file `app.py`.

8. **App secrets** (app → Settings → Secrets):
   ```toml
   GH_TOKEN  = "github_pat_xxxxxxxxxxxx"
   DATA_REPO = "<YOU>/trading-data"
   ```

Done. The site auto-detects where it's running: local bot folders on this PC,
the GitHub data repo in the cloud. Data on the website lags the bots by at
most ~15 min (sync) + ~2 min (cache).

### Privacy

- Deploying from a **private** repo keeps the app unlisted, and you can
  restrict viewers to specific emails in the app settings (free tier allows
  one private app — exactly this one).
- The data repo only ever receives journals/portfolios — never `.env`,
  tokens, or logs.
