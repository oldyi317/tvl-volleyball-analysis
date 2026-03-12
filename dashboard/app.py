"""
TVL 企業排球聯賽 — 女子組互動儀表板 v5 (色彩與資料清洗優化版)
"""
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 設定根目錄
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import PROCESSED_DIR, MODELS_DIR, WOMEN_TEAMS, STAT_COLUMNS, SEASON

# ======== 頁面配置 ========
st.set_page_config(page_title="TVL 女子組數據分析", page_icon="🏐", layout="wide", initial_sidebar_state="expanded")

# ======== 顏色設定 (依照用戶色號調整) ========
TEAM_COLORS = {name: info["color"] for name, info in WOMEN_TEAMS.items()}
POS_COLORS = {"主攻手": "#E63946", "中間手": "#457B9D", "舉球員": "#2A9D8F",
              "自由球員": "#E9C46A", "副攻手": "#F4A261"}

# 雷達圖專用高對比配色
RADAR_BG_COLOR = "rgb(12, 56, 117)"    # 深藍背景
LEAGUE_AVG_COLOR = "rgb(255, 215, 0)"  # 聯盟平均 (亮黃)
POS_AVG_COLOR = "rgb(255, 69, 0)"      # 位置平均 (鮮橘紅)
COMPARE_COLOR_A = "rgb(0, 191, 255)"   # 同隊比較A (亮藍)
COMPARE_COLOR_B = "rgb(50, 205, 50)"   # 同隊比較B (亮綠)

def _hex_to_rgba(hex_color: str, alpha: float = 0.2) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

# ======== 數據載入與清洗 ========
@st.cache_data
def load_data():
    p_path = PROCESSED_DIR / "players_clean.csv"
    m_path = PROCESSED_DIR / "matches_clean.csv"
    s_path = PROCESSED_DIR / "player_stats_summary.csv"
    if not p_path.exists(): return None

    players = pd.read_csv(p_path)
    matches = pd.read_csv(m_path, parse_dates=["比賽日期"]) if m_path.exists() else pd.DataFrame()
    summary = pd.read_csv(s_path) if s_path.exists() else pd.DataFrame()

    # 1. 解決攻擊手問題：統一清洗位置名稱
    if "位置" in players.columns:
        players["位置"] = players["位置"].replace("攻擊手", "主攻手")
    if "位置" in summary.columns:
        summary["位置"] = summary["位置"].replace("攻擊手", "主攻手")

    for df in [players, matches, summary]:
        if not df.empty and "球隊" not in df.columns: df["球隊"] = "未知"

    if not summary.empty and "player_id" in summary.columns and "player_id" in players.columns:
        team_map = players.set_index("player_id")["球隊"].to_dict()
        summary["球隊"] = summary["player_id"].map(team_map).fillna("未知")
        pos_map = players.set_index("player_id")["位置"].to_dict()
        summary["位置"] = summary["player_id"].map(pos_map)

    return {"players": players, "matches": matches, "summary": summary}

# ======== CSS 視覺強化 ========
def inject_css():
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap');
    html, body, [class*="st-"] { font-family: 'Noto Sans TC', sans-serif; font-size: 18px; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a2a3a 0%, #0f1923 100%);
        border: 2px solid rgba(74,144,217,0.3); border-radius: 15px; padding: 20px !important;
    }
    div[data-testid="stMetricValue"] { font-size: 2.3rem !important; font-weight: 800 !important; color: #ffffff !important; }
    button[data-baseweb="tab"] p { font-size: 1.25rem !important; font-weight: 700 !important; }
    </style>""", unsafe_allow_html=True)

# ======== 篩選邏輯 ========
def apply_filters(data, team_filter, pos_filter, season_filter=None):
    p, m, s = data["players"].copy(), data["matches"].copy(), data["summary"].copy()
    if season_filter and season_filter != "全部賽季":
        if "季" in m.columns: m = m[m["季"] == season_filter]
        if "季" in s.columns: s = s[s["季"] == season_filter]
    if team_filter != "全聯盟":
        p = p[p["球隊"] == team_filter]
        m = m[m["球隊"] == team_filter]
        s = s[s["球隊"] == team_filter]
    if pos_filter != "全部位置":
        p = p[p["位置"] == pos_filter]
        s = s[s["位置"] == pos_filter]
    return {"players": p, "matches": m, "summary": s}

# ======== 分頁: 球員分析 ========
def page_player(data, raw_data):
    p, s = data["players"], data["summary"]
    if p.empty: return st.warning("無符合條件球員")
    opts = {f"#{int(r['背號'])} {r['姓名']} ({r.get('球隊','')})": idx for idx, r in p.iterrows()}
    player = p.loc[opts[st.selectbox("🔍 選擇球員", list(opts.keys()))]]
    t_color = TEAM_COLORS.get(player.get("球隊", ""), "#4A90D9")

    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.markdown(f'<div style="background: linear-gradient(135deg, {t_color}33, {t_color}66); border: 3px solid {t_color}; border-radius: 20px; padding: 40px; text-align: center;"><div style="font-size: 80px; font-weight: 900; color: {t_color};">#{int(player.get("背號", 0))}</div><div style="font-size: 45px; font-weight: 800; color: white;">{player["姓名"]}</div><div style="font-size: 22px; color: #ddd;">{player.get("球隊", "")} | {player.get("位置", "")}</div></div>', unsafe_allow_html=True)

    with c2:
        st.subheader("🎯 技術雷達圖")
        rs = raw_data["summary"]
        ps = s[s["player_id"] == player["player_id"]]
        if not ps.empty:
            ps = ps.iloc[0]
            lbls, vals, l_avg, p_avg = [], [], [], []
            for col in STAT_COLUMNS:
                pct = f"{col}%"
                if pct in ps.index and pd.notna(ps[pct]):
                    lbls.append(col); vals.append(float(ps[pct]))
                    l_avg.append(float(rs[pct].mean())); p_avg.append(float(rs[rs["位置"] == player["位置"]][pct].mean()))
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=vals+[vals[0]], theta=lbls+[lbls[0]], fill="toself", name="個人", line=dict(color=t_color, width=6)))
            fig.add_trace(go.Scatterpolar(r=p_avg+[p_avg[0]], theta=lbls+[lbls[0]], name=f"{player['位置']}平均", line=dict(color=POS_AVG_COLOR, width=3, dash="dot")))
            fig.add_trace(go.Scatterpolar(r=l_avg+[l_avg[0]], theta=lbls+[lbls[0]], name="聯盟平均", line=dict(color=LEAGUE_AVG_COLOR, width=3, dash="dash")))
            fig.update_layout(polar=dict(bgcolor=RADAR_BG_COLOR, radialaxis=dict(range=[0,100], tickfont_size=14, gridcolor="rgba(255,255,255,0.2)"), angularaxis=dict(tickfont=dict(size=20, weight="bold", color="white"))), height=550, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
            st.plotly_chart(fig, use_container_width=True)

# ======== 分頁: 戰力對比 ========
def page_compare(data):
    p, s = data["players"], data["summary"]
    c1, c2 = st.columns(2)
    opts = {f"#{int(r['背號'])} {r['姓名']} ({r.get('球隊','')})": r["player_id"] for _, r in p.iterrows()}
    pa_id = opts[c1.selectbox("🏐 球員 A", list(opts.keys()), index=0)]
    pb_id = opts[c2.selectbox("🏐 球員 B", list(opts.keys()), index=min(1, len(opts)-1))]
    
    sa, sb = s[s["player_id"] == pa_id].iloc[0], s[s["player_id"] == pb_id].iloc[0]
    pa, pb = p[p["player_id"] == pa_id].iloc[0], p[p["player_id"] == pb_id].iloc[0]

    # 解決同隊顏色問題
    color_a, color_b = TEAM_COLORS.get(pa['球隊'],"#fff"), TEAM_COLORS.get(pb['球隊'],"#fff")
    if pa['球隊'] == pb['球隊']: color_a, color_b = COMPARE_COLOR_A, COMPARE_COLOR_B

    lbls, v_a, v_b = [], [], []
    for col in STAT_COLUMNS:
        pct = f"{col}%"
        if pd.notna(sa.get(pct)) and pd.notna(sb.get(pct)):
            lbls.append(col); v_a.append(float(sa[pct])); v_b.append(float(sb[pct]))
            
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=v_a+[v_a[0]], theta=lbls+[lbls[0]], fill="toself", name=pa['姓名'], line=dict(color=color_a, width=5)))
    fig.add_trace(go.Scatterpolar(r=v_b+[v_b[0]], theta=lbls+[lbls[0]], fill="toself", name=pb['姓名'], line=dict(color=color_b, width=5)))
    fig.update_layout(polar=dict(bgcolor=RADAR_BG_COLOR, angularaxis=dict(tickfont_size=20, color="white")), height=550, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
    st.plotly_chart(fig, use_container_width=True)

# ======== 主程式 ========
def main():
    inject_css()
    raw = load_data()
    if raw is None: return st.error("資料遺失")
    
    st.sidebar.markdown("# 🏐 TVL 數據分析")
    t_filter = st.sidebar.selectbox("🏢 選擇球隊", ["全聯盟"] + list(WOMEN_TEAMS.keys()))
    p_filter = st.sidebar.selectbox("🏃 篩選位置", ["全部位置"] + list(POS_COLORS.keys()))
    
    data = apply_filters(raw, t_filter, p_filter)
    tabs = st.tabs(["📊 總覽", "🏃 分析", "⚔️ 對比"])
    with tabs[1]: page_player(data, raw)
    with tabs[2]: page_compare(data)

if __name__ == "__main__": main()