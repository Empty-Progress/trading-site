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
        print("No changes since last sync.")
        return

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


if __name__ == "__main__":
    main()
