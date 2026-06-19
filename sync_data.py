"""
=============================================================
DATA SYNC — pushes bot data to the private GitHub data repo
so the Streamlit Cloud website can read it.

Copies only the small files the website needs (journals,
portfolios, filter attribution). Never copies .env or logs.

Run manually:   python sync_data.py
Scheduled:      Task Scheduler, every 15 minutes
=============================================================
"""

import glob
import os
import shutil
import subprocess
import sys
from datetime import datetime

# Local clone of the private data repo (create with:
#   git clone https://github.com/<you>/trading-data C:\Users\Cloudius\trading-data )
DATA_REPO_DIR = r"C:\Users\Cloudius\trading-data"

SOURCES = {
    "tc":     r"C:\Users\Cloudius\OneDrive\Documents\TC_Capital\tc_capital_data\trades",
    "martan": r"C:\Users\Cloudius\OneDrive\Documents\Martan_Trading\martan_trading_data\trades",
}

PATTERNS = ("*_journal.csv", "*_portfolio.json", "filter_attribution.csv")

# Bot source code repo — keeps a backup of the .py files in sync
BOTS_REPO_DIR = r"C:\Users\Cloudius\OneDrive\Documents\trading-bots"
BOT_CODE_SOURCES = {
    "TC_Capital":     (r"C:\Users\Cloudius\OneDrive\Documents\TC_Capital",     "tc_"),
    "Martan_Trading": (r"C:\Users\Cloudius\OneDrive\Documents\Martan_Trading", "martan_"),
}


def main():
    if not os.path.isdir(os.path.join(DATA_REPO_DIR, ".git")):
        print(f"ERROR: {DATA_REPO_DIR} is not a git repo. Clone the data repo there first.")
        sys.exit(1)

    copied = 0
    for system, src in SOURCES.items():
        dest = os.path.join(DATA_REPO_DIR, system)
        os.makedirs(dest, exist_ok=True)
        for pattern in PATTERNS:
            for path in glob.glob(os.path.join(src, pattern)):
                shutil.copy2(path, os.path.join(dest, os.path.basename(path)))
                copied += 1
    print(f"Copied {copied} files.")

    def git(*args):
        return subprocess.run(["git", "-C", DATA_REPO_DIR] + list(args),
                              capture_output=True, text=True)

    git("add", "-A")
    diff = git("diff", "--cached", "--quiet")
    if diff.returncode == 0:
        print("Data: no changes since last sync.")
    else:
        msg = f"data sync {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        commit = git("commit", "-m", msg)
        if commit.returncode != 0:
            print("Commit failed:", commit.stderr)
            sys.exit(1)
        push = git("push")
        if push.returncode != 0:
            print("Push failed:", push.stderr)
            sys.exit(1)
        print(f"Pushed: {msg}")

    # Always sync bot code regardless of whether data changed
    sync_bot_code()


def sync_bot_code():
    if not os.path.isdir(os.path.join(BOTS_REPO_DIR, ".git")):
        print("trading-bots repo not found, skipping code sync.")
        return

    copied = 0
    for folder, (src_dir, prefix) in BOT_CODE_SOURCES.items():
        dest_dir = os.path.join(BOTS_REPO_DIR, folder)
        os.makedirs(dest_dir, exist_ok=True)
        for f in os.listdir(src_dir):
            if f.endswith(".py") and f.startswith(prefix):
                shutil.copy2(os.path.join(src_dir, f), os.path.join(dest_dir, f))
                copied += 1

    def git(*args):
        return subprocess.run(["git", "-C", BOTS_REPO_DIR] + list(args),
                              capture_output=True, text=True)

    git("add", "-A")
    diff = git("diff", "--cached", "--quiet")
    if diff.returncode == 0:
        print("Bot code: no changes since last sync.")
        return

    msg = f"code sync {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    commit = git("commit", "-m", msg)
    if commit.returncode != 0:
        print("Bot code commit failed:", commit.stderr)
        return
    push = git("push")
    if push.returncode != 0:
        print("Bot code push failed:", push.stderr)
        return
    print(f"Bot code pushed: {msg}")


if __name__ == "__main__":
    main()
