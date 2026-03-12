"""
TVL 企業排球聯賽 — 女子組互動儀表板 v3 (視覺強化版)
優化內容：大幅提升字體大小、強化圖表對比度、優化指標卡片
"""
import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from config.settings import PROCESSED_DIR, MODELS_DIR, WOMEN_TEAMS, STAT_COLUMNS, SEASON, PLAYOFF_TAGS

# ======== Page config ========
st.set_page_config(page_title="TVL 女子組數據儀表板", page_icon="🏐", layout="wide", initial_sidebar_state="expanded")

# ======== Colors ========
TEAM_COLORS = {name: info["color"] for name, info in WOMEN_TEAMS.items()}
POS_COLORS = {"主攻手": "#E63946", "中間手": "#457B9D", "舉球員": "#2A9D8F",
              "自由球員": "#E9C46A", "副攻手": "#F4A261", "攻擊手": "#8338EC"}

def _hex_to_rgba(hex_color: str, alpha: float = 0.2) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

# ======== Data loading ========
@st.cache_data
def load_data():
    p_path = PROCESSED_DIR / "players_clean.csv"
    m_path = PROCESSED_DIR / "matches_clean.csv"
    s_path = PROCESSED_DIR / "player_stats_summary.csv"
    if not p_path.exists():
        return None

    players = pd.read_csv(p_path)
    matches = pd.read_csv(m_path, parse_dates=["比賽日期"]) if m_path.exists() else pd.DataFrame()
    summary = pd.read_csv(s_path) if s_path.exists() else pd.DataFrame()

    for df in [players, matches, summary]:
        if not df.empty and "球隊" not in df.columns:
            df["球隊"] = "未知"

    if not summary.empty and "player_id" in summary.columns and "player_id" in players.columns:
        if summary["球隊"].eq("未知").all() or summary["球隊"].isna().all():
            team_map = players.set_index("player_id")["球隊"].to_dict()
            summary["球隊"] = summary["player_id"].map(team_map).fillna("未知")

    if not summary.empty and "位置" not in summary.columns and "player_id" in summary.columns:
        if "player_id" in players.columns and "位置" in players.columns:
            pos_map = players.set_index("player_id")["位置"].to_dict()
            summary["位置"] = summary["player_id"].map(pos_map)

    return {"players": players, "matches": matches, "summary": summary}

# ======== CSS ========
def inject_css():
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap');
    
    /* 全局字體設定 */
    html, body, [class*="st-"] { 
        font-family: 'Noto Sans TC', sans-serif; 
        font-size: 18px; /* 提升基礎字體 */
    }
    
    /* 側邊欄文字放大 */
    section[data-testid="stSidebar"] .stText, section[data-testid="stSidebar"] label {
        font-size: 1.1rem !important;
        font-weight: 500 !important;
    }

    /* 指標 (Metric) 強化 */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a2a3a 0%, #0f1923 100%);
        border: 2px solid rgba(74,144,217,0.3);
        border_radius: 15px;
        padding: 20px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 1.1rem !important;
        color: #a0aec0 !important;
        margin-bottom: 8px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
    }
    
    /* Tabs 文字放大 */
    button[data-baseweb="tab"] p {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }
    </style>""", unsafe_allow_html=True)

# ======== Filters ========
def apply_filters(data, team_filter, pos_filter, season_filter=None):
    players = data["players"].copy()
    matches = data["matches"].copy()
    summary = data["summary"].copy()

    if season_filter and season_filter != "全部賽季":
        if "季" in matches.columns: matches = matches[matches["季"] == season_filter]
        if "季" in summary.columns: summary = summary[summary["季"] == season_filter]

    if team_filter != "全聯盟":
        if "球隊" in players.columns: players = players[players["球隊"] == team_filter]
        if "球隊" in matches.columns: matches = matches[matches["球隊"] == team_filter]
        if "球隊" in summary.columns: summary = summary[summary["球隊"] == team_filter]

    if pos_filter != "全部位置":
        if "位置" in players.columns: players = players[players["位置"] == pos_filter]
        if "位置" in summary.columns: summary = summary[summary["位置"] == pos_filter]
        if "player_id" in players.columns and "player_id" in matches.columns:
            matches = matches[matches["player_id"].isin(players["player_id"])]

    return {"players": players, "matches": matches, "summary": summary}

# ======== Page: Overview ========
def page_overview(data, raw_data):
    players, summary = data["players"], data["summary"]

    cols = st.columns(4)
    cols[0].metric("🏐 球員人數", f"{len(players)} 人")
    if "身高(cm)" in players.columns:
        cols[1].metric("📏 平均身高", f"{players['身高(cm)'].mean():.1f} cm")
    if "年齡" in players.columns:
        cols[2].metric("📅 平均年齡", f"{players['年齡'].mean():.1f} 歲")
    if not summary.empty and "得分" in summary.columns:
        top = summary.loc[summary["得分"].idxmax()]
        name_col = "球員姓名" if "球員姓名" in summary.columns else "姓名"
        cols[3].metric("👑 得分王", f"{top.get(name_col, '?')}", f"{int(top['得分'])} 分")

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏆 得分排行 (Top 10)")
        if not summary.empty and "得分" in summary.columns:
            name_col = "球員姓名" if "球員姓名" in summary.columns else "姓名"
            top10 = summary.nlargest(10, "得分").copy()
            top10["label"] = top10.apply(lambda r: f"#{int(r.get('球員背號', 0))} {r[name_col]}", axis=1)
            fig = px.bar(top10, y="label", x="得分", orientation="h",
                         color="球隊", color_discrete_map=TEAM_COLORS, text="得分")
            fig.update_traces(textposition="outside", textfont_size=14)
            fig.update_layout(yaxis=dict(autorange="reversed", tickfont_size=14), 
                              xaxis=dict(title_font_size=16), height=500)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🏃 位置組成")
        if "位置" in players.columns:
            pos_counts = players["位置"].value_counts().reset_index()
            pos_counts.columns = ["位置", "人數"]
            fig = px.pie(pos_counts, values="人數", names="位置",
                         color="位置", color_discrete_map=POS_COLORS, hole=0.4)
            fig.update_traces(textinfo='percent+label', textfont_size=15)
            fig.update_layout(height=500, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# ======== Page: Player Analysis ========
def page_player(data, raw_data):
    players, summary = data["players"], data["summary"]
    if players.empty:
        st.warning("此篩選條件下沒有球員")
        return

    # 球員選擇器加大文字
    player_options = {f"#{int(r['背號'])} {r['姓名']} ({r.get('球隊','')})": idx
                      for idx, r in players.iterrows()}
    selected_label = st.selectbox("🔍 選擇球員", list(player_options.keys()))
    p = players.loc[player_options[selected_label]]
    team_color = TEAM_COLORS.get(p.get("球隊", ""), "#4A90D9")

    col1, col2 = st.columns([1, 1.5])

    with col1:
        # 球員卡強化
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {team_color}33, {team_color}66);
                    border: 3px solid {team_color}; border-radius: 20px;
                    padding: 40px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.2);">
            <div style="font-size: 72px; font-weight: 900; color: {team_color}; line-height: 1;">#{int(p.get('背號', 0))}</div>
            <div style="font-size: 42px; font-weight: 800; margin: 15px 0; color: white;">{p['姓名']}</div>
            <div style="font-size: 20px; color: #eee; background: rgba(0,0,0,0.2); 
                        display: inline-block; padding: 5px 20px; border-radius: 50px;">
                {p.get('球隊', '')} | {p.get('位置', '')}
            </div>
        </div>""", unsafe_allow_html=True)
        st.write("")

        # 身體素質
        body_cols = st.columns(2)
        metrics = [("身高", "身高(cm)", "cm"), ("體重", "體重(kg)", "kg"),
                   ("攻擊高度", "攻擊高度(cm)", "cm"), ("攔網高度", "攔網高度(cm)", "cm")]
        for i, (label, key, unit) in enumerate(metrics):
            val = p.get(key, None)
            if pd.notna(val):
                body_cols[i % 2].metric(label, f"{int(val)} {unit}")

    with col2:
        st.subheader("🎯 技術指標對比")
        pid = p.get("player_id", p.name)
        player_summary = summary[summary["player_id"] == pid]
        
        if not player_summary.empty:
            ps = player_summary.iloc[0]
            labels, values, league_avg, pos_avg = [], [], [], []
            player_pos = p.get("位置", "")
            raw_summary = raw_data["summary"] 
            
            for col in STAT_COLUMNS:
                pct = f"{col}%"
                if pct in ps.index and pd.notna(ps[pct]):
                    labels.append(col)
                    values.append(float(ps[pct]))
                    league_avg.append(float(raw_summary[pct].mean()) if pct in raw_summary.columns else 0)
                    pos_data = raw_summary[raw_summary["位置"] == player_pos] if "位置" in raw_summary.columns else pd.DataFrame()
                    pos_avg.append(float(pos_data[pct].mean()) if not pos_data.empty and pct in pos_data.columns else 0)

            if len(labels) >= 3:
                fig = go.Figure()
                # 球員數據
                fig.add_trace(go.Scatterpolar(
                    r=values + [values[0]], theta=labels + [labels[0]],
                    fill="toself", name=f"{p['姓名']} (個人)",
                    line=dict(color=team_color, width=6),
                    fillcolor=_hex_to_rgba(team_color, 0.4)))
                # 同位置平均
                fig.add_trace(go.Scatterpolar(
                    r=pos_avg + [pos_avg[0]], theta=labels + [labels[0]],
                    name=f"{player_pos} 平均",
                    line=dict(color="#FFD700", width=3, dash="dot")))
                # 全聯盟平均
                fig.add_trace(go.Scatterpolar(
                    r=league_avg + [league_avg[0]], theta=labels + [labels[0]],
                    name="全聯盟平均",
                    line=dict(color="#FFFFFF", width=2, dash="dash")))

                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 100], tickfont_size=14, gridcolor="rgba(255,255,255,0.1)"),
                        angularaxis=dict(tickfont=dict(size=18, color="white", weight="bold"), rotation=90)),
                    font=dict(size=16),
                    height=550, margin=dict(l=80, r=80, t=20, b=20),
                    legend=dict(font_size=16, orientation="h", y=-0.1, x=0.5, xanchor="center"),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("此球員尚無賽季彙總數據")

# ======== Main ========
def main():
    inject_css()
    raw_data = load_data()
    if raw_data is None:
        st.error("⚠️ 找不到資料！")
        return

    # Sidebar
    st.sidebar.markdown("# 🏐 TVL 女子組數據")
    st.sidebar.markdown(f"**賽季：{SEASON}**")
    st.sidebar.divider()

    team_options = ["全聯盟"] + list(WOMEN_TEAMS.keys())
    team_filter = st.sidebar.selectbox("🏢 選擇隊伍", team_options)

    if team_filter != "全聯盟":
        color = TEAM_COLORS.get(team_filter, "#1B3A6B")
        st.sidebar.markdown(f'<div style="width:100%;height:8px;background:{color};border-radius:4px;margin-bottom:20px;"></div>', unsafe_allow_html=True)
        
        team_players = raw_data["players"][raw_data["players"]["球隊"] == team_filter]
        st.sidebar.info(f"**{team_filter} 快速摘要**\n\n- 球員人數：{len(team_players)} 人\n- 平均身高：{team_players['身高(cm)'].mean():.1f} cm")

    pos_options = ["全部位置"] + list(POS_COLORS.keys())
    pos_filter = st.sidebar.selectbox("🏃 篩選位置", pos_options)

    season_options = ["全部賽季"]
    if "季" in raw_data["summary"].columns:
        season_options += sorted(raw_data["summary"]["季"].dropna().unique().tolist(), reverse=True)
    season_filter = st.sidebar.selectbox("📅 選擇賽季", season_options, index=1 if len(season_options)>1 else 0)

    data = apply_filters(raw_data, team_filter, pos_filter, season_filter)

    # Tabs
    tabs = st.tabs(["📊 總覽", "🏃 球員分析", "⚔️ 球員比較", "📈 比賽趨勢", "🤖 ML 洞察"])
    with tabs[0]: page_overview(data, raw_data)
    with tabs[1]: page_player(data, raw_data)
    with tabs[2]: st.write("（球員比較頁面建構中...）")
    with tabs[3]: st.write("（趨勢分析頁面建構中...）")
    with tabs[4]: page_ml_insights = None # 簡化版

if __name__ == "__main__":
    main()