"""
=============================================================
TC CAPITAL + MARTAN TRADING — SHARED SITE LIBRARY
=============================================================
Dual-mode data loading:
 - LOCAL:  reads the live bot folders on this PC (when they exist)
 - CLOUD:  reads the private GitHub data repo via the API, using
           GH_TOKEN + DATA_REPO from Streamlit secrets
=============================================================
"""

import hmac
import os
import io
import glob
import json
import streamlit as st
import pandas as pd
import requests

COMPETITION_START = "2026-05-26"

LOCAL_FOLDERS = {
    "tc":     r"C:\Users\Cloudius\OneDrive\Documents\TC_Capital\tc_capital_data\trades",
    "martan": r"C:\Users\Cloudius\OneDrive\Documents\Martan_Trading\martan_trading_data\trades",
}

# Colours
TC_GOLD     = "#C9A84C"
MARTAN_BLUE = "#4DB8FF"
WIN_GREEN   = "#10B981"
LOSS_RED    = "#EF4444"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Playfair+Display:wght@600;700;800;900&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
  background:
    radial-gradient(ellipse 70% 45% at 15% -5%, rgba(201,168,76,0.10), transparent),
    radial-gradient(ellipse 70% 45% at 85% -5%, rgba(77,184,255,0.10), transparent),
    linear-gradient(180deg, #0A1322 0%, #070D18 60%, #060B14 100%);
  color: #F0EDE6;
}
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }

h1, h2, h3 { font-family: 'Playfair Display', serif !important; }

/* ---- sidebar ---- */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0C1628 0%, #091120 100%);
  border-right: 1px solid #16283F;
}
[data-testid="stSidebar"] * { color: #C0D0E0; }
[data-testid="stSidebarNav"] a {
  border-radius: 8px; margin: 2px 8px; transition: background .15s;
}
[data-testid="stSidebarNav"] a:hover { background: rgba(42,79,122,0.30); }
[data-testid="stSidebarNav"] span { font-family: 'DM Mono', monospace; font-size: 0.85rem; letter-spacing: 0.04em; }

/* ---- metric tiles ---- */
[data-testid="metric-container"], div[data-testid="stMetric"] {
  background: linear-gradient(160deg, #101C32 0%, #0B1424 100%);
  border: 1px solid #1E3A5F; border-radius: 14px; padding: 14px 16px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04);
}
[data-testid="stMetricValue"] { font-family: 'Playfair Display', serif !important; font-weight: 700 !important; font-size: 1.35rem !important; }
[data-testid="stMetricLabel"] { font-size: 0.62rem !important; text-transform: uppercase; letter-spacing: 0.12em; font-family: 'DM Mono', monospace !important; color: #6A8CAA !important; }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #080E1C; }
::-webkit-scrollbar-thumb { background: #2A4F7A; border-radius: 3px; }

/* ---- score cards ---- */
.score-box { border-radius: 18px; padding: 32px 24px 26px; text-align: center; position: relative;
  backdrop-filter: blur(6px); transition: box-shadow .3s; }
.tc-box {
  background: linear-gradient(150deg, rgba(201,168,76,0.10) 0%, rgba(13,24,48,0.92) 45%), #0D1830;
  border: 1px solid rgba(201,168,76,0.50);
  box-shadow: 0 0 26px rgba(201,168,76,0.10), inset 0 1px 0 rgba(255,255,255,0.05);
}
.martan-box {
  background: linear-gradient(150deg, rgba(77,184,255,0.10) 0%, rgba(10,22,40,0.92) 45%), #0A1628;
  border: 1px solid rgba(77,184,255,0.50);
  box-shadow: 0 0 26px rgba(77,184,255,0.10), inset 0 1px 0 rgba(255,255,255,0.05);
}
.score-box.leading.tc-box  { border-color: #C9A84C; box-shadow: 0 0 46px rgba(201,168,76,0.30), inset 0 1px 0 rgba(255,255,255,0.06); }
.score-box.leading.martan-box { border-color: #4DB8FF; box-shadow: 0 0 46px rgba(77,184,255,0.30), inset 0 1px 0 rgba(255,255,255,0.06); }
.lead-badge {
  position: absolute; top: -12px; left: 50%; transform: translateX(-50%);
  padding: 3px 16px; border-radius: 999px; font-family: 'DM Mono', monospace;
  font-size: 0.6rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.14em;
  white-space: nowrap;
}
.lead-badge.gold { background: linear-gradient(90deg, #8A6D2F, #C9A84C, #E8CD7E); color: #0B1426; box-shadow: 0 2px 12px rgba(201,168,76,0.45); }
.lead-badge.blue { background: linear-gradient(90deg, #2A7CB0, #4DB8FF, #9CDBFF); color: #06121F; box-shadow: 0 2px 12px rgba(77,184,255,0.45); }

.score-label { font-family: 'DM Mono', monospace; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.18em; margin-bottom: 6px; }
.score-name { font-family: 'Playfair Display', serif; font-size: 1.55rem; font-weight: 700; margin-bottom: 14px; }
.score-pnl { font-family: 'Playfair Display', serif; font-size: 3.1rem; font-weight: 800; line-height: 1; text-shadow: 0 2px 18px rgba(0,0,0,0.45); }
.score-zar { font-family: 'DM Mono', monospace; font-size: 0.95rem; margin-top: 8px; opacity: 0.65; }

/* ---- VS circle ---- */
.vs-box { text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.vs-circle {
  width: 62px; height: 62px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: radial-gradient(circle at 32% 28%, #16283F, #0B1426);
  border: 1px solid #243F5F;
  font-family: 'Playfair Display', serif; font-size: 1.25rem; font-weight: 800; color: #6A8CAA;
  box-shadow: 0 0 22px rgba(90,140,200,0.18), inset 0 1px 0 rgba(255,255,255,0.06);
}

/* ---- leader banner ---- */
.leader-banner {
  border-radius: 999px; padding: 10px 24px; text-align: center;
  font-family: 'DM Mono', monospace; font-size: 0.78rem; letter-spacing: 0.12em;
  text-transform: uppercase; margin: 4px auto 22px; max-width: 560px;
  animation: bannerpulse 3.2s ease-in-out infinite;
}
@keyframes bannerpulse {
  0%, 100% { filter: brightness(1); }
  50%      { filter: brightness(1.22); }
}

/* ---- stats table ---- */
.metric-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 9px 14px; border-radius: 9px; margin-bottom: 2px;
  font-family: 'DM Mono', monospace; font-size: 0.78rem;
  border-bottom: 1px solid #14233A; transition: background .15s;
}
.metric-row:hover { background: rgba(30,58,95,0.28); }
.metric-name { color: #5A8CAA; }

.section-header {
  font-family: 'DM Mono', monospace; font-size: 0.64rem; text-transform: uppercase;
  letter-spacing: 0.18em; color: #4A6E92; margin: 26px 0 10px 0; padding-bottom: 6px;
  border-bottom: 1px solid transparent;
  border-image: linear-gradient(90deg, #2A4F7A 0%, rgba(42,79,122,0) 70%) 1;
}

/* ---- trade rows ---- */
.trade-row {
  display: flex; gap: 12px; align-items: center; justify-content: space-between;
  background: linear-gradient(90deg, #0E1828 0%, #0C1422 100%);
  border: 1px solid #15263E; border-radius: 10px;
  padding: 8px 14px; margin-bottom: 6px;
  font-family: 'DM Mono', monospace; font-size: 0.72rem;
  transition: transform .12s, border-color .12s;
}
.trade-row:hover { transform: translateX(3px); border-color: #2A4F7A; }
.dir-pill {
  padding: 2px 11px; border-radius: 999px; font-size: 0.6rem; font-weight: 600; letter-spacing: 0.1em;
}
.dir-pill.buy  { background: rgba(16,185,129,0.14); color: #10B981; border: 1px solid rgba(16,185,129,0.40); }
.dir-pill.sell { background: rgba(239,68,68,0.14);  color: #EF4444; border: 1px solid rgba(239,68,68,0.40); }

.timer-text { font-family: 'DM Mono', monospace; font-size: 0.7rem; color: #3A5A7A; text-align: center; margin-bottom: 20px; }

/* ---- password gate ---- */
.pw-card {
  max-width: 420px; margin: 8vh auto 0; padding: 42px 36px 34px;
  border-radius: 18px; text-align: center;
  background: linear-gradient(160deg, #0F1B32 0%, #0A1322 100%);
  border: 1px solid #1E3A5F;
  box-shadow: 0 18px 60px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.05);
}
.pw-emblem { font-size: 2.2rem; margin-bottom: 10px; }
.pw-title { font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 800; color: #E8E2D4; margin-bottom: 4px; }
.pw-sub { font-family: 'DM Mono', monospace; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.16em; color: #4A6E92; }
[data-testid="stTextInput"] input {
  background: #0B1426 !important; border: 1px solid #1E3A5F !important; border-radius: 10px !important;
  color: #F0EDE6 !important; font-family: 'DM Mono', monospace !important; text-align: center;
}
[data-testid="stTextInput"] input:focus { border-color: #C9A84C !important; box-shadow: 0 0 0 1px #C9A84C33 !important; }

/* ---- mobile ---- */
@media (max-width: 768px) {
  .score-pnl  { font-size: 2rem; }
  .score-name { font-size: 1.05rem; }
  .score-box  { padding: 20px 12px 16px; min-width: unset; }
  .score-meta { font-size: 0.72rem; }
  .lead-badge { font-size: 0.58rem; padding: 3px 10px; top: -12px; }
  .leader-banner { font-size: 0.62rem; padding: 7px 12px; letter-spacing: 0.06em; }
  .vs-circle  { width: 52px; height: 52px; font-size: 1rem; margin: 12px auto; }
  .dir-pill   { font-size: 0.6rem; padding: 1px 6px; }
  .trade-row  { font-size: 0.72rem; padding: 6px 8px; flex-wrap: wrap; gap: 4px; }
  .context-tile { padding: 10px 8px; }
  .context-val  { font-size: 1.2rem; }
  .context-lbl  { font-size: 0.65rem; }
  /* prevent horizontal scroll on tables */
  [data-testid="stDataFrame"], [data-testid="stTable"] { overflow-x: auto; font-size: 0.72rem; }
  /* stack Plotly charts properly */
  [data-testid="stPlotlyChart"] { margin: 0 -8px; }
}
</style>
"""


def require_password():
    """Password gate. Active only when APP_PASSWORD is set in secrets,
    so local use (no secrets file) is never blocked."""
    pw = _secret("APP_PASSWORD")
    if not pw:
        return
    if st.session_state.get("auth_ok"):
        return
    st.markdown("""
    <div class='pw-card'>
      <div class='pw-emblem'>⚔</div>
      <div class='pw-title'>TC Capital&nbsp;vs&nbsp;Martan Trading</div>
      <div class='pw-sub'>Private scoreboard — enter password</div>
    </div>
    """, unsafe_allow_html=True)
    _, mid, _ = st.columns([2, 1.6, 2])
    with mid:
        entered = st.text_input("Password", type="password", label_visibility="collapsed",
                                placeholder="••••••••")
        if entered:
            if hmac.compare_digest(entered, pw):
                st.session_state["auth_ok"] = True
                st.rerun()
            else:
                st.error("Incorrect password")
    st.stop()


def page_setup(title, icon):
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    require_password()


def is_local():
    return os.path.isdir(LOCAL_FOLDERS["tc"])


def _secret(key, default=None):
    try:
        return st.secrets[key]
    except Exception:
        return default


# =============================================================
# REMOTE (GitHub data repo) ACCESS
# =============================================================

def _gh_headers(raw=False):
    h = {"Accept": "application/vnd.github.raw" if raw else "application/vnd.github+json"}
    token = _secret("GH_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


@st.cache_data(ttl=120, show_spinner=False)
def _gh_list(folder):
    repo = _secret("DATA_REPO")
    r = requests.get(f"https://api.github.com/repos/{repo}/contents/{folder}",
                     headers=_gh_headers(), timeout=20)
    r.raise_for_status()
    return [f["path"] for f in r.json() if f["type"] == "file"]


@st.cache_data(ttl=120, show_spinner=False)
def _gh_fetch(path):
    repo = _secret("DATA_REPO")
    r = requests.get(f"https://api.github.com/repos/{repo}/contents/{path}",
                     headers=_gh_headers(raw=True), timeout=20)
    r.raise_for_status()
    return r.text


# =============================================================
# DATA LOADING (works in both modes)
# =============================================================

@st.cache_data(ttl=60, show_spinner=False)
def load_journals(system):
    """All journal rows for one system, with instrument_key column."""
    dfs = []
    if is_local():
        for path in glob.glob(os.path.join(LOCAL_FOLDERS[system], "*_journal.csv")):
            try:
                df = pd.read_csv(path)
                if df.empty or len(df.columns) < 2:
                    continue
                df["instrument_key"] = os.path.basename(path).replace("_journal.csv", "")
                dfs.append(df)
            except Exception:
                continue
    else:
        for path in _gh_list(system):
            name = os.path.basename(path)
            if not name.endswith("_journal.csv"):
                continue
            try:
                df = pd.read_csv(io.StringIO(_gh_fetch(path)))
                if df.empty or len(df.columns) < 2:
                    continue
                df["instrument_key"] = name.replace("_journal.csv", "")
                dfs.append(df)
            except Exception:
                continue
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


@st.cache_data(ttl=60, show_spinner=False)
def load_portfolios(system):
    """instrument -> portfolio dict for one system."""
    out = {}
    if is_local():
        for path in glob.glob(os.path.join(LOCAL_FOLDERS[system], "*_portfolio.json")):
            try:
                with open(path, encoding="utf-8") as f:
                    out[os.path.basename(path).replace("_portfolio.json", "")] = json.load(f)
            except Exception:
                continue
    else:
        for path in _gh_list(system):
            name = os.path.basename(path)
            if not name.endswith("_portfolio.json"):
                continue
            try:
                out[name.replace("_portfolio.json", "")] = json.loads(_gh_fetch(path))
            except Exception:
                continue
    return out


def get_closed_trades(df, since=None):
    if df.empty:
        return pd.DataFrame()
    closed = df[df["type"] == "CLOSE"].copy()
    for col in ("pnl_usd", "pnl_zar", "capital_after_usd"):
        if col in closed.columns:
            closed[col] = pd.to_numeric(closed[col], errors="coerce").fillna(0)
    # Competition rule: a trade counts if it was ENTERED on/after the start date
    if since and "entry_date" in closed.columns:
        closed = closed[closed["entry_date"] >= since]
    return closed.sort_values("exit_date").reset_index(drop=True)


def calc_metrics(trades):
    empty = {
        "total": 0, "wins": 0, "losses": 0,
        "win_rate": 0.0, "total_pnl_usd": 0.0, "total_pnl_zar": 0.0,
        "avg_pnl": 0.0, "profit_factor": 0.0,
        "best": 0.0, "worst": 0.0, "max_dd": 0.0,
        "setups": 0, "setup_wins": 0, "setup_win_rate": 0.0,
    }
    if trades.empty:
        return empty

    total  = len(trades)
    wins   = trades[trades["pnl_usd"] > 0]
    losses = trades[trades["pnl_usd"] < 0]

    setup_pnl  = trades.groupby(["instrument_key", "entry_date", "direction"])["pnl_usd"].sum()
    setups     = len(setup_pnl)
    setup_wins = int((setup_pnl > 0).sum())

    gross_profit = wins["pnl_usd"].sum()
    gross_loss   = abs(losses["pnl_usd"].sum())
    pf = gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)

    cum  = trades["pnl_usd"].cumsum()
    dd   = (cum - cum.cummax()).min()

    return {
        "total":          total,
        "wins":           len(wins),
        "losses":         len(losses),
        "win_rate":       len(wins) / total * 100 if total else 0.0,
        "total_pnl_usd":  trades["pnl_usd"].sum(),
        "total_pnl_zar":  trades["pnl_zar"].sum(),
        "avg_pnl":        trades["pnl_usd"].mean(),
        "profit_factor":  pf,
        "best":           trades["pnl_usd"].max(),
        "worst":          trades["pnl_usd"].min(),
        "max_dd":         dd,
        "setups":         setups,
        "setup_wins":     setup_wins,
        "setup_win_rate": setup_wins / setups * 100 if setups else 0.0,
    }


def fmt_pnl(v, prefix="$"):
    sign = "+" if v >= 0 else ""
    return f"{prefix}{sign}{v:.2f}"


def fmt_pf(v):
    if v == float("inf"):
        return "∞"
    return f"{v:.2f}×"


def pnl_colour(v):
    if v > 0:
        return WIN_GREEN
    if v < 0:
        return LOSS_RED
    return "#6A8CAA"


# =============================================================
# PER-BOT PAGE (shared by the TC Capital and Martan pages)
# =============================================================

def render_bot_page(system, name, accent, tagline):
    import time
    from datetime import datetime
    import plotly.graph_objects as go

    page_setup(f"{name} — Performance", "📈")

    raw        = load_journals(system)
    portfolios = load_portfolios(system)
    closed     = get_closed_trades(raw)
    comp       = get_closed_trades(raw, since=COMPETITION_START)
    m_all      = calc_metrics(closed)
    m_comp     = calc_metrics(comp)

    capital  = sum(p.get("capital_usd", 0) for p in portfolios.values())
    starting = sum(p.get("starting_capital", 0) for p in portfolios.values())
    open_trades = []
    for inst, p in portfolios.items():
        for t in p.get("open_trades", []):
            t = dict(t)
            t["instrument"] = inst
            open_trades.append(t)

    st.markdown(f"""
    <div style='text-align:center; margin-bottom:4px;'>
      <span style='font-family:"Playfair Display",serif; font-size:2rem; font-weight:800; color:{accent};'>{name}</span>
    </div>
    <div class='timer-text'>{tagline} &nbsp;·&nbsp; Updated {datetime.now().strftime("%d %b %Y %H:%M:%S")} &nbsp;·&nbsp; Auto-refreshes every 60s</div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    cap_delta = capital - starting
    c1.metric("Total Capital",     f"${capital:,.2f}", fmt_pnl(cap_delta))
    c2.metric("Competition P&L",   fmt_pnl(m_comp["total_pnl_usd"]))
    c3.metric("All-Time P&L",      fmt_pnl(m_all["total_pnl_usd"]))
    c4.metric("Setup Win Rate",    f"{m_comp['setup_win_rate']:.0f}%",
              f"{m_comp['setups']} setups")
    c5.metric("Profit Factor",     fmt_pf(m_comp["profit_factor"]))
    c6.metric("Open Positions",    str(len(open_trades)))

    # ---- Equity curve ----
    st.markdown("<div class='section-header'>Cumulative P&L — All Time</div>", unsafe_allow_html=True)
    if not closed.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=closed["exit_date"], y=closed["pnl_usd"].cumsum(),
            name=name, line=dict(color=accent, width=2.6, shape="spline", smoothing=0.6),
            mode="lines", fill="tozeroy",
            fillcolor=f"rgba({int(accent[1:3],16)},{int(accent[3:5],16)},{int(accent[5:7],16)},0.08)",
            hovertemplate="%{x}<br>P&L: $%{y:+.2f}<extra></extra>",
        ))
        fig.add_hline(y=0, line_dash="dot", line_color="#2A3A50", line_width=1)
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#080E1C",
            font=dict(family="DM Mono, monospace", color="#5A8CAA", size=11),
            xaxis=dict(gridcolor="#1A2A3A", linecolor="#1A2A3A"),
            yaxis=dict(gridcolor="#1A2A3A", linecolor="#1A2A3A", tickprefix="$", tickformat=".2f"),
            margin=dict(l=10, r=10, t=20, b=10), height=300, showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("<div style='text-align:center; padding:40px; font-family:\"DM Mono\",monospace; font-size:0.8rem; color:#3A5A7A;'>No closed trades yet</div>",
                    unsafe_allow_html=True)

    # ---- Per-instrument table ----
    st.markdown("<div class='section-header'>Per Instrument</div>", unsafe_allow_html=True)
    rows = []
    for inst in sorted(portfolios.keys()):
        p = portfolios[inst]
        inst_closed = closed[closed["instrument_key"] == inst] if not closed.empty else pd.DataFrame()
        inst_comp   = comp[comp["instrument_key"] == inst] if not comp.empty else pd.DataFrame()
        rows.append({
            "Instrument":      p.get("name", inst.upper()),
            "Capital":         round(p.get("capital_usd", 0), 2),
            "All-Time P&L":    round(float(inst_closed["pnl_usd"].sum()) if not inst_closed.empty else 0.0, 2),
            "Competition P&L": round(float(inst_comp["pnl_usd"].sum()) if not inst_comp.empty else 0.0, 2),
            "Unit Exits":      len(inst_closed),
            "Open Units":      len(p.get("open_trades", [])),
        })
    if rows:
        df_inst = pd.DataFrame(rows)
        st.dataframe(
            df_inst,
            use_container_width=True, hide_index=True,
            column_config={
                "Capital":         st.column_config.NumberColumn(format="$%.2f"),
                "All-Time P&L":    st.column_config.NumberColumn(format="$%.2f"),
                "Competition P&L": st.column_config.NumberColumn(format="$%.2f"),
            },
        )

    # ---- Open positions ----
    st.markdown("<div class='section-header'>Open Positions</div>", unsafe_allow_html=True)
    if open_trades:
        df_open = pd.DataFrame(open_trades)
        keep = [c for c in ("instrument", "direction", "unit", "entry_date", "entry_price",
                            "stop_loss", "take_profit", "size") if c in df_open.columns]
        st.dataframe(df_open[keep] if keep else df_open,
                     use_container_width=True, hide_index=True)
    else:
        st.markdown("<div style='text-align:center; padding:20px; font-family:\"DM Mono\",monospace; font-size:0.75rem; color:#3A5A7A;'>No open positions</div>",
                    unsafe_allow_html=True)

    # ---- Recent trades ----
    st.markdown("<div class='section-header'>Recent Closed Trades</div>", unsafe_allow_html=True)
    if not closed.empty:
        recent = closed.sort_values("exit_date", ascending=False).head(12)
        for _, row in recent.iterrows():
            pnl     = float(row.get("pnl_usd", 0))
            col     = WIN_GREEN if pnl >= 0 else LOSS_RED
            sign    = "+" if pnl >= 0 else ""
            inst    = str(row.get("instrument_key", "?")).upper()
            unit    = str(row.get("unit", "?"))
            reason  = str(row.get("exit_reason", ""))
            date    = str(row.get("exit_date", ""))[:16]
            direct  = str(row.get("direction", ""))
            pill    = "buy" if direct == "BUY" else "sell"
            st.markdown(f"""
            <div class='trade-row' style='border-left: 3px solid {col};'>
              <span style='color:#5A8CAA;'>{date}</span>
              <span class='dir-pill {pill}'>{direct}</span>
              <span style='color:#C0D0E0;'>{inst} U{unit}</span>
              <span style='color:#5A8CAA; font-size:0.65rem;'>{reason}</span>
              <span style='color:{col}; font-weight:600;'>${sign}{pnl:.2f}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align:center; padding:20px; font-family:\"DM Mono\",monospace; font-size:0.75rem; color:#3A5A7A;'>No trades yet</div>",
                    unsafe_allow_html=True)

    time.sleep(60)
    st.rerun()
