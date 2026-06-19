"""
=============================================================
TC CAPITAL vs MARTAN TRADING — COMBINED SITE
Front page: head-to-head scoreboard
Pages: TC Capital | Martan Trading (sidebar navigation)

Local:  python -m streamlit run app.py --server.port 8504
Cloud:  deploy this folder's repo on share.streamlit.io
=============================================================
"""

import time
from datetime import datetime, date

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

import lib
from lib import (COMPETITION_START, TC_GOLD, MARTAN_BLUE, WIN_GREEN, LOSS_RED,
                 fmt_pnl, fmt_pf)

lib.page_setup("TC vs Martan — Scoreboard", "⚔")

# =============================================================
# LOAD DATA
# =============================================================

tc_raw     = lib.load_journals("tc")
martan_raw = lib.load_journals("martan")

tc_all      = lib.get_closed_trades(tc_raw)
martan_all  = lib.get_closed_trades(martan_raw)
tc_comp     = lib.get_closed_trades(tc_raw,     since=COMPETITION_START)
martan_comp = lib.get_closed_trades(martan_raw, since=COMPETITION_START)

tc_m         = lib.calc_metrics(tc_comp)
martan_m     = lib.calc_metrics(martan_comp)
tc_all_m     = lib.calc_metrics(tc_all)
martan_all_m = lib.calc_metrics(martan_all)

# =============================================================
# HEADER
# =============================================================

now_str      = datetime.now().strftime("%d %b %Y  %H:%M:%S")
start_dt     = datetime.strptime(COMPETITION_START, "%Y-%m-%d")
days_running = (datetime.now() - start_dt).days

st.markdown(f"""
<div style='text-align:center; margin-bottom:8px;'>
  <span style='font-family:"Playfair Display",serif; font-size:2rem; font-weight:800; color:#C0D0E0; letter-spacing:0.05em;'>
    ⚔&nbsp; TC Capital &nbsp;vs&nbsp; Martan Trading &nbsp;⚔
  </span>
</div>
<div class='timer-text'>
  Competition started {COMPETITION_START} &nbsp;·&nbsp; Day {days_running + 1} &nbsp;·&nbsp; Updated {now_str} &nbsp;·&nbsp; Auto-refreshes every 60s
</div>
""", unsafe_allow_html=True)

tc_pnl     = tc_m["total_pnl_usd"]
martan_pnl = martan_m["total_pnl_usd"]

if tc_m["total"] == 0 and martan_m["total"] == 0:
    banner_bg, banner_col = "#1A2A40", "#5A8CAA"
    banner_txt = "Competition underway — waiting for first trades"
elif tc_pnl > martan_pnl:
    banner_bg, banner_col = "#0D2010", TC_GOLD
    banner_txt = f"🏆  TC Capital leading by ${tc_pnl - martan_pnl:+.2f}"
elif martan_pnl > tc_pnl:
    banner_bg, banner_col = "#0A1828", MARTAN_BLUE
    banner_txt = f"🏆  Martan Trading leading by ${martan_pnl - tc_pnl:+.2f}"
else:
    banner_bg, banner_col = "#1A2A40", "#C0D0E0"
    banner_txt = "Dead heat — level pegging"

st.markdown(f"""
<div class='leader-banner' style='background:{banner_bg}; color:{banner_col}; border: 1px solid {banner_col}33;'>
  {banner_txt}
</div>
""", unsafe_allow_html=True)

# =============================================================
# SCOREBOARD ROW
# =============================================================

col_tc, col_vs, col_mt = st.columns([5, 1, 5])

tc_leading = tc_pnl > martan_pnl
mt_leading = martan_pnl > tc_pnl
tc_badge = "<div class='lead-badge gold'>★ Leading</div>" if tc_leading else ""
mt_badge = "<div class='lead-badge blue'>★ Leading</div>" if mt_leading else ""

with col_tc:
    tc_col  = WIN_GREEN if tc_pnl >= 0 else LOSS_RED
    tc_sign = "+" if tc_pnl >= 0 else ""
    st.markdown(f"""
    <div class='score-box tc-box{" leading" if tc_leading else ""}'>
      {tc_badge}
      <div class='score-label' style='color:{TC_GOLD};'>TC Capital</div>
      <div class='score-name' style='color:{TC_GOLD};'>The Base System</div>
      <div class='score-pnl' style='color:{tc_col};'>${tc_sign}{tc_pnl:.2f}</div>
      <div class='score-zar' style='color:{tc_col};'>R{tc_sign}{tc_m["total_pnl_zar"]:.2f}</div>
      <div style='font-family:"DM Mono",monospace; font-size:0.72rem; color:#5A8CAA; margin-top:12px;'>
        {tc_m["setups"]} setups ({tc_m["total"]} unit exits) &nbsp;·&nbsp; {tc_m["setup_win_rate"]:.0f}% setup win rate
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_vs:
    st.markdown("""
    <div class='vs-box' style='height:100%; min-height:170px;'>
      <div class='vs-circle'>VS</div>
    </div>
    """, unsafe_allow_html=True)

with col_mt:
    mt_col  = WIN_GREEN if martan_pnl >= 0 else LOSS_RED
    mt_sign = "+" if martan_pnl >= 0 else ""
    st.markdown(f"""
    <div class='score-box martan-box{" leading" if mt_leading else ""}'>
      {mt_badge}
      <div class='score-label' style='color:{MARTAN_BLUE};'>Martan Trading</div>
      <div class='score-name' style='color:{MARTAN_BLUE};'>The Upgraded System</div>
      <div class='score-pnl' style='color:{mt_col};'>${mt_sign}{martan_pnl:.2f}</div>
      <div class='score-zar' style='color:{mt_col};'>R{mt_sign}{martan_m["total_pnl_zar"]:.2f}</div>
      <div style='font-family:"DM Mono",monospace; font-size:0.72rem; color:#5A8CAA; margin-top:12px;'>
        {martan_m["setups"]} setups ({martan_m["total"]} unit exits) &nbsp;·&nbsp; {martan_m["setup_win_rate"]:.0f}% setup win rate
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================
# CUMULATIVE P&L CHART
# =============================================================

st.markdown("<div class='section-header'>Cumulative P&L — Competition Period</div>", unsafe_allow_html=True)

fig = go.Figure()

if not tc_comp.empty:
    fig.add_trace(go.Scatter(
        x=tc_comp["exit_date"], y=tc_comp["pnl_usd"].cumsum(),
        name="TC Capital",
        line=dict(color=TC_GOLD, width=2.6, shape="spline", smoothing=0.6),
        mode="lines+markers", marker=dict(size=5, color=TC_GOLD),
        fill="tozeroy", fillcolor="rgba(201,168,76,0.07)",
        hovertemplate="<b>TC Capital</b><br>%{x}<br>P&L: $%{y:+.2f}<extra></extra>",
    ))

if not martan_comp.empty:
    fig.add_trace(go.Scatter(
        x=martan_comp["exit_date"], y=martan_comp["pnl_usd"].cumsum(),
        name="Martan Trading",
        line=dict(color=MARTAN_BLUE, width=2.6, shape="spline", smoothing=0.6),
        mode="lines+markers", marker=dict(size=5, color=MARTAN_BLUE),
        fill="tozeroy", fillcolor="rgba(77,184,255,0.07)",
        hovertemplate="<b>Martan Trading</b><br>%{x}<br>P&L: $%{y:+.2f}<extra></extra>",
    ))

fig.add_hline(y=0, line_dash="dot", line_color="#2A3A50", line_width=1)
fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#080E1C",
    font=dict(family="DM Mono, monospace", color="#5A8CAA", size=11),
    xaxis=dict(gridcolor="#1A2A3A", linecolor="#1A2A3A", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="#1A2A3A", linecolor="#1A2A3A", showgrid=True, zeroline=False,
               tickprefix="$", tickformat=".2f"),
    margin=dict(l=10, r=10, t=20, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1A2A3A",
                font=dict(size=11, color="#8AAAC0"), orientation="h", y=-0.15),
    height=300,
)

if tc_comp.empty and martan_comp.empty:
    st.markdown("""
    <div style='text-align:center; padding:60px; font-family:"DM Mono",monospace;
         font-size:0.8rem; color:#3A5A7A; border:1px dashed #1A2A40; border-radius:8px;'>
      No competition trades yet — chart will appear when the first trade closes
    </div>
    """, unsafe_allow_html=True)
else:
    st.plotly_chart(fig, use_container_width=True)

# =============================================================
# METRICS TABLE
# =============================================================

st.markdown("<div class='section-header'>Head-to-Head Stats — Competition Period</div>",
            unsafe_allow_html=True)

def metric_row(label, tc_val, mt_val, tc_better_fn=None, fmt_fn=str):
    tc_str = fmt_fn(tc_val)
    mt_str = fmt_fn(mt_val)
    if tc_better_fn:
        tc_wins = tc_better_fn(tc_val, mt_val)
        mt_wins = tc_better_fn(mt_val, tc_val)
        tc_col  = WIN_GREEN if tc_wins else ("#6A8CAA" if tc_val == mt_val else LOSS_RED)
        mt_col  = WIN_GREEN if mt_wins else ("#6A8CAA" if tc_val == mt_val else LOSS_RED)
    else:
        tc_col, mt_col = TC_GOLD, MARTAN_BLUE
    st.markdown(f"""
    <div class='metric-row'>
      <span style='color:{tc_col}; width:30%; text-align:right; font-weight:600;'>{tc_str}</span>
      <span class='metric-name' style='width:40%; text-align:center;'>{label}</span>
      <span style='color:{mt_col}; width:30%; text-align:left; font-weight:600;'>{mt_str}</span>
    </div>
    """, unsafe_allow_html=True)

higher_is_better = lambda a, b: a > b

metric_row("Total P&L (USD)",    tc_m["total_pnl_usd"],  martan_m["total_pnl_usd"],
           higher_is_better, lambda v: fmt_pnl(v))
metric_row("Total P&L (ZAR)",    tc_m["total_pnl_zar"],  martan_m["total_pnl_zar"],
           higher_is_better, lambda v: fmt_pnl(v, "R"))
metric_row("Setups Taken",       tc_m["setups"],          martan_m["setups"],
           None, str)
metric_row("Setup Win Rate",     tc_m["setup_win_rate"],  martan_m["setup_win_rate"],
           higher_is_better, lambda v: f"{v:.1f}%")
metric_row("Unit Win Rate",      tc_m["win_rate"],        martan_m["win_rate"],
           higher_is_better, lambda v: f"{v:.1f}%")
metric_row("Unit Exits",         tc_m["total"],           martan_m["total"],
           None, str)
metric_row("Unit Wins / Losses", f"{tc_m['wins']}W / {tc_m['losses']}L",
           f"{martan_m['wins']}W / {martan_m['losses']}L", None, str)
metric_row("Avg P&L per Unit",   tc_m["avg_pnl"],         martan_m["avg_pnl"],
           higher_is_better, lambda v: fmt_pnl(v))
metric_row("Profit Factor",      tc_m["profit_factor"],   martan_m["profit_factor"],
           higher_is_better, fmt_pf)
metric_row("Best Trade",         tc_m["best"],            martan_m["best"],
           higher_is_better, lambda v: fmt_pnl(v))
metric_row("Worst Trade",        tc_m["worst"],           martan_m["worst"],
           higher_is_better, lambda v: fmt_pnl(v))
metric_row("Max Drawdown",       tc_m["max_dd"],          martan_m["max_dd"],
           higher_is_better, lambda v: fmt_pnl(v))

# =============================================================
# WEEKLY P&L BREAKDOWN
# =============================================================

st.markdown("<div class='section-header'>Weekly P&L — Competition Period</div>",
            unsafe_allow_html=True)

tc_weekly     = lib.weekly_pnl(tc_comp)
martan_weekly = lib.weekly_pnl(martan_comp)

all_weeks = sorted(set(
    list(tc_weekly["week_start"]) + list(martan_weekly["week_start"])
))

if all_weeks:
    tc_w   = dict(zip(tc_weekly["week_start"],     tc_weekly["pnl"]))
    mart_w = dict(zip(martan_weekly["week_start"], martan_weekly["pnl"]))

    week_labels, tc_vals_w, mart_vals_w = [], [], []
    table_rows = []
    for ws in all_weeks:
        we      = ws + pd.Timedelta(days=6)
        lbl     = f"{ws.strftime('%d %b')} – {we.strftime('%d %b')}"
        tc_v    = tc_w.get(ws, 0.0)
        mart_v  = mart_w.get(ws, 0.0)
        week_labels.append(lbl)
        tc_vals_w.append(tc_v)
        mart_vals_w.append(mart_v)
        if tc_v > mart_v:
            winner = f"<span style='color:{TC_GOLD};'>TC Capital</span>"
        elif mart_v > tc_v:
            winner = f"<span style='color:{MARTAN_BLUE};'>Martan</span>"
        else:
            winner = "<span style='color:#6A8CAA;'>Draw</span>"
        table_rows.append((lbl, tc_v, mart_v, winner))

    # Grouped bar chart
    fig_w = go.Figure()
    fig_w.add_trace(go.Bar(
        x=week_labels, y=tc_vals_w, name="TC Capital",
        marker_color=[WIN_GREEN if v >= 0 else LOSS_RED for v in tc_vals_w],
        marker_line_color=TC_GOLD, marker_line_width=1.2, opacity=0.88,
    ))
    fig_w.add_trace(go.Bar(
        x=week_labels, y=mart_vals_w, name="Martan Trading",
        marker_color=[WIN_GREEN if v >= 0 else LOSS_RED for v in mart_vals_w],
        marker_line_color=MARTAN_BLUE, marker_line_width=1.2, opacity=0.70,
    ))
    fig_w.add_hline(y=0, line_dash="dot", line_color="#2A3A50", line_width=1)
    fig_w.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#080E1C",
        font=dict(family="DM Mono, monospace", color="#5A8CAA", size=11),
        xaxis=dict(gridcolor="#1A2A3A", linecolor="#1A2A3A"),
        yaxis=dict(gridcolor="#1A2A3A", linecolor="#1A2A3A",
                   tickprefix="$", tickformat=".2f"),
        margin=dict(l=10, r=10, t=20, b=10),
        barmode="group", bargap=0.22, bargroupgap=0.08,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11, color="#8AAAC0"),
                    orientation="h", y=-0.22),
        height=260,
    )
    st.plotly_chart(fig_w, use_container_width=True)

    # Weekly table
    header = (
        "<div class='metric-row' style='border-bottom:1px solid #1E3A5F; margin-bottom:4px;'>"
        f"<span style='color:#4A6E92; width:36%; text-align:left;'>WEEK</span>"
        f"<span style='color:{TC_GOLD}; width:22%; text-align:right;'>TC CAPITAL</span>"
        f"<span style='color:{MARTAN_BLUE}; width:22%; text-align:right;'>MARTAN</span>"
        f"<span style='color:#4A6E92; width:20%; text-align:center;'>WINNER</span>"
        "</div>"
    )
    st.markdown(header, unsafe_allow_html=True)
    for lbl, tc_v, mart_v, winner in table_rows:
        tc_col   = WIN_GREEN if tc_v   >= 0 else LOSS_RED
        mart_col = WIN_GREEN if mart_v >= 0 else LOSS_RED
        st.markdown(f"""
        <div class='metric-row'>
          <span style='color:#5A8CAA; width:36%; text-align:left;'>{lbl}</span>
          <span style='color:{tc_col}; width:22%; text-align:right; font-weight:600;'>{fmt_pnl(tc_v)}</span>
          <span style='color:{mart_col}; width:22%; text-align:right; font-weight:600;'>{fmt_pnl(mart_v)}</span>
          <span style='width:20%; text-align:center;'>{winner}</span>
        </div>
        """, unsafe_allow_html=True)

    # Weekly totals row
    tc_tot   = sum(tc_vals_w)
    mart_tot = sum(mart_vals_w)
    tc_tot_c   = WIN_GREEN if tc_tot   >= 0 else LOSS_RED
    mart_tot_c = WIN_GREEN if mart_tot >= 0 else LOSS_RED
    if tc_tot > mart_tot:
        tot_winner = f"<span style='color:{TC_GOLD}; font-weight:700;'>TC Capital</span>"
    elif mart_tot > tc_tot:
        tot_winner = f"<span style='color:{MARTAN_BLUE}; font-weight:700;'>Martan</span>"
    else:
        tot_winner = "<span style='color:#6A8CAA;'>Draw</span>"
    st.markdown(f"""
    <div class='metric-row' style='border-top:1px solid #1E3A5F; margin-top:4px; background:rgba(20,35,60,0.4);'>
      <span style='color:#C0D0E0; width:36%; text-align:left; font-weight:700; letter-spacing:0.06em;'>TOTAL</span>
      <span style='color:{tc_tot_c}; width:22%; text-align:right; font-weight:700;'>{fmt_pnl(tc_tot)}</span>
      <span style='color:{mart_tot_c}; width:22%; text-align:right; font-weight:700;'>{fmt_pnl(mart_tot)}</span>
      <span style='width:20%; text-align:center;'>{tot_winner}</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<div style='text-align:center; padding:30px; font-family:\"DM Mono\",monospace; font-size:0.8rem; color:#3A5A7A;'>No trades yet in competition period</div>",
                unsafe_allow_html=True)

# =============================================================
# PER-INSTRUMENT BREAKDOWN
# =============================================================

st.markdown("<div class='section-header'>P&L by Instrument — Competition Period</div>",
            unsafe_allow_html=True)

all_instruments = sorted(set(
    list(tc_comp["instrument_key"].unique() if not tc_comp.empty else []) +
    list(martan_comp["instrument_key"].unique() if not martan_comp.empty else [])
))

if all_instruments:
    tc_vals, mt_vals = [], []
    for inst in all_instruments:
        tc_vals.append(tc_comp[tc_comp["instrument_key"] == inst]["pnl_usd"].sum() if not tc_comp.empty else 0)
        mt_vals.append(martan_comp[martan_comp["instrument_key"] == inst]["pnl_usd"].sum() if not martan_comp.empty else 0)

    labels = [i.upper() for i in all_instruments]
    fig_inst = go.Figure()
    fig_inst.add_trace(go.Bar(
        x=labels, y=tc_vals, name="TC Capital",
        marker_color=[WIN_GREEN if v >= 0 else LOSS_RED for v in tc_vals],
        marker_line_color=TC_GOLD, marker_line_width=1, opacity=0.85,
    ))
    fig_inst.add_trace(go.Bar(
        x=labels, y=mt_vals, name="Martan Trading",
        marker_color=[WIN_GREEN if v >= 0 else LOSS_RED for v in mt_vals],
        marker_line_color=MARTAN_BLUE, marker_line_width=1, opacity=0.65,
    ))
    fig_inst.add_hline(y=0, line_dash="dot", line_color="#2A3A50", line_width=1)
    fig_inst.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#080E1C",
        font=dict(family="DM Mono, monospace", color="#5A8CAA", size=11),
        xaxis=dict(gridcolor="#1A2A3A", linecolor="#1A2A3A"),
        yaxis=dict(gridcolor="#1A2A3A", linecolor="#1A2A3A", tickprefix="$", tickformat=".2f"),
        margin=dict(l=10, r=10, t=20, b=10),
        barmode="group", bargap=0.25, bargroupgap=0.08,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11, color="#8AAAC0"),
                    orientation="h", y=-0.2),
        height=280,
    )
    st.plotly_chart(fig_inst, use_container_width=True)
else:
    st.markdown("<div style='text-align:center; padding:30px; font-family:\"DM Mono\",monospace; font-size:0.8rem; color:#3A5A7A;'>No instrument data yet</div>",
                unsafe_allow_html=True)

# =============================================================
# RECENT TRADES
# =============================================================

st.markdown("<div class='section-header'>Recent Trades</div>", unsafe_allow_html=True)

col_l, col_r = st.columns(2)

def render_recent_trades(trades, colour, name):
    if trades.empty:
        st.markdown("<div style='text-align:center; padding:20px; font-family:\"DM Mono\",monospace; font-size:0.75rem; color:#3A5A7A;'>No trades yet</div>",
                    unsafe_allow_html=True)
        return
    recent = trades.sort_values("exit_date", ascending=False).head(8)
    st.markdown(f"<div style='font-family:\"DM Mono\",monospace; font-size:0.65rem; color:{colour}; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:6px;'>{name}</div>",
                unsafe_allow_html=True)
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

with col_l:
    render_recent_trades(tc_comp, TC_GOLD, "TC Capital")
with col_r:
    render_recent_trades(martan_comp, MARTAN_BLUE, "Martan Trading")

# =============================================================
# ALL-TIME CONTEXT
# =============================================================

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<div class='section-header'>All-Time Context</div>", unsafe_allow_html=True)

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("TC All-Time P&L",       fmt_pnl(tc_all_m["total_pnl_usd"]))
c2.metric("TC Setup Win Rate",     f"{tc_all_m['setup_win_rate']:.0f}%")
c3.metric("TC Total Setups",       str(tc_all_m["setups"]))
c4.metric("Martan All-Time P&L",   fmt_pnl(martan_all_m["total_pnl_usd"]))
c5.metric("Martan Setup Win Rate", f"{martan_all_m['setup_win_rate']:.0f}%")
c6.metric("Martan Total Setups",   str(martan_all_m["setups"]))

# =============================================================
# AUTO REFRESH (sleep + rerun — script tags don't run in st.markdown)
# =============================================================

time.sleep(60)
st.rerun()
