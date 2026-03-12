"""
TVL 企業排球聯賽 — 女子組互動儀表板 v2 (UI 優化版)
優化內容：同位置雷達圖對比、側邊欄隊伍摘要、各隊穩定度箱型圖
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
    html, body, [class*="st-"] { font-family: 'Noto Sans TC', 'Microsoft JhengHei', sans-serif; }
    .main .block-container { padding-top: 1.5rem; max-width: 1400px; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #0f1923 0%, #1a2d42 100%);
        border: 1px solid rgba(74,144,217,0.15); border-radius: 12px; padding: 16px 20px;
    }
    div[data-testid="stMetric"] label { color: #8899aa !important; font-size: 0.85rem; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #fff !important; font-weight: 800; }
    </style>""", unsafe_allow_html=True)

# ======== Filters ========
def apply_filters(data, team_filter, pos_filter, season_filter=None):
    players = data["players"].copy()
    matches = data["matches"].copy()
    summary = data["summary"].copy()

    if season_filter and season_filter != "全部賽季":
        if "季" in matches.columns:
            matches = matches[matches["季"] == season_filter]
        if "季" in summary.columns:
            summary = summary[summary["季"] == season_filter]

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
        st.subheader("得分排行")
        if not summary.empty and "得分" in summary.columns:
            name_col = "球員姓名" if "球員姓名" in summary.columns else "姓名"
            top10 = summary.nlargest(10, "得分").copy()
            top10["label"] = top10.apply(lambda r: f"#{int(r.get('球員背號', 0))} {r[name_col]}", axis=1)
            fig = px.bar(top10, y="label", x="得分", orientation="h",
                         color="球隊", color_discrete_map=TEAM_COLORS)
            fig.update_layout(yaxis=dict(autorange="reversed"), height=400,
                              margin=dict(l=0, r=20, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("位置組成")
        if "位置" in players.columns:
            pos_counts = players["位置"].value_counts().reset_index()
            pos_counts.columns = ["位置", "人數"]
            fig = px.pie(pos_counts, values="人數", names="位置",
                         color="位置", color_discrete_map=POS_COLORS, hole=0.4)
            fig.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("📊 各隊技術指標穩定度分析")
    # 使用原始彙總數據來進行跨隊比較
    full_summary = raw_data["summary"]
    if not full_summary.empty:
        stat_to_plot = st.selectbox("選擇分析指標", [f"{c}%" for c in STAT_COLUMNS if f"{c}%" in full_summary.columns])
        fig = px.box(full_summary, x="球隊", y=stat_to_plot, color="球隊",
                     color_discrete_map=TEAM_COLORS, points="all",
                     title=f"{stat_to_plot} 數據分佈 (點代表個別球員)")
        fig.update_layout(height=450, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

# ======== Page: Player Analysis ========
def page_player(data, raw_data):
    players, summary = data["players"], data["summary"]
    if players.empty:
        st.warning("此篩選條件下沒有球員")
        return

    player_options = {f"#{int(r['背號'])} {r['姓名']} ({r.get('球隊','')})": idx
                      for idx, r in players.iterrows()}
    selected_label = st.selectbox("選擇球員", list(player_options.keys()))
    p = players.loc[player_options[selected_label]]
    team_color = TEAM_COLORS.get(p.get("球隊", ""), "#4A90D9")

    col1, col2 = st.columns([2, 3])

    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {team_color}22, {team_color}44);
                    border: 2px solid {team_color}; border-radius: 16px;
                    padding: 24px; text-align: center;">
            <div style="font-size: 48px; font-weight: 900; color: {team_color};">#{int(p.get('背號', 0))}</div>
            <div style="font-size: 28px; font-weight: 800; margin: 4px 0;">{p['姓名']}</div>
            <div style="font-size: 14px; color: #999; margin-bottom: 12px;">
                {p.get('球隊', '')} · {p.get('位置', '')}
            </div>
        </div>""", unsafe_allow_html=True)

        body_cols = st.columns(2)
        for i, (label, key) in enumerate([("身高", "身高(cm)"), ("體重", "體重(kg)"),
                                           ("攻擊高度", "攻擊高度(cm)"), ("攔網高度", "攔網高度(cm)")]):
            val = p.get(key, None)
            if pd.notna(val):
                unit = "cm" if "cm" in str(key) else "kg"
                body_cols[i % 2].metric(label, f"{int(val)} {unit}")
        if pd.notna(p.get("MBTI")):
            st.metric("MBTI", p["MBTI"])

    with col2:
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
                    # 全聯盟平均基準線
                    league_avg.append(float(raw_summary[pct].mean()) if pct in raw_summary.columns else 0)
                    # 同位置平均基準線
                    pos_data = raw_summary[raw_summary["位置"] == player_pos] if "位置" in raw_summary.columns else pd.DataFrame()
                    pos_avg.append(float(pos_data[pct].mean()) if not pos_data.empty and pct in pos_data.columns else 0)

            if len(labels) >= 3:
                fig = go.Figure()
                # 1. 球員本人數據
                fig.add_trace(go.Scatterpolar(
                    r=values + [values[0]], theta=labels + [labels[0]],
                    fill="toself", name=p["姓名"],
                    line=dict(color=team_color, width=4),
                    fillcolor=_hex_to_rgba(team_color, 0.35)))
                
                # 2. 同位置平均 (新加入)
                fig.add_trace(go.Scatterpolar(
                    r=pos_avg + [pos_avg[0]], theta=labels + [labels[0]],
                    name=f"{player_pos} 平均",
                    line=dict(color="#FFB703", width=2, dash="dot")))
                
                # 3. 全聯盟平均
                fig.add_trace(go.Scatterpolar(
                    r=league_avg + [league_avg[0]], theta=labels + [labels[0]],
                    name="全聯盟平均",
                    line=dict(color="#AAAAAA", width=2, dash="dash")))

                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(150,150,150,0.2)"),
                        angularaxis=dict(gridcolor="rgba(150,150,150,0.2)")),
                    height=450, margin=dict(l=60, r=60, t=40, b=40),
                    legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="center", x=0.5))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("此球員尚無賽季彙總數據")

# ======== Page: Player Compare (保持原樣或微調) ========
def page_compare(data):
    players, summary = data["players"], data["summary"]
    if players.empty or summary.empty:
        st.warning("資料不足")
        return

    col1, col2 = st.columns(2)
    player_opts = {f"#{int(r['背號'])} {r['姓名']} ({r.get('球隊','')})": r.get("player_id", idx)
                   for idx, r in players.iterrows()}
    opts_list = list(player_opts.keys())

    with col1: label_a = st.selectbox("球員 A", opts_list, index=0)
    with col2: label_b = st.selectbox("球員 B", opts_list, index=min(1, len(opts_list) - 1))

    pid_a, pid_b = player_opts[label_a], player_opts[label_b]
    sa = summary[summary["player_id"] == pid_a]
    sb = summary[summary["player_id"] == pid_b]
    if sa.empty or sb.empty:
        st.warning("所選球員缺少數據")
        return

    sa, sb = sa.iloc[0], sb.iloc[0]
    pa = players[players["player_id"] == pid_a].iloc[0]
    pb = players[players["player_id"] == pid_b].iloc[0]

    col_radar, col_table = st.columns([1, 1])
    with col_radar:
        labels, vals_a, vals_b = [], [], []
        for col in STAT_COLUMNS:
            pct = f"{col}%"
            va, vb = sa.get(pct), sb.get(pct)
            if pd.notna(va) and pd.notna(vb):
                labels.append(col); vals_a.append(float(va)); vals_b.append(float(vb))

        if len(labels) >= 3:
            color_a = TEAM_COLORS.get(pa.get("球隊", ""), "#4A90D9")
            color_b = TEAM_COLORS.get(pb.get("球隊", ""), "#E65100")
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=vals_a+[vals_a[0]], theta=labels+[labels[0]], fill="toself", name=pa["姓名"], line=dict(color=color_a, width=3)))
            fig.add_trace(go.Scatterpolar(r=vals_b+[vals_b[0]], theta=labels+[labels[0]], fill="toself", name=pb["姓名"], line=dict(color=color_b, width=3)))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=420)
            st.plotly_chart(fig, use_container_width=True)

    with col_table:
        rows = []
        for col in STAT_COLUMNS:
            pct = f"{col}%"
            va, vb = sa.get(pct), sb.get(pct)
            va_str = f"{va:.1f}%" if pd.notna(va) else "-"
            vb_str = f"{vb:.1f}%" if pd.notna(vb) else "-"
            winner = pa["姓名"] if pd.notna(va) and pd.notna(vb) and va > vb else (pb["姓名"] if pd.notna(va) and pd.notna(vb) and vb > va else "-")
            rows.append({"指標": f"{col}效率", pa["姓名"]: va_str, pb["姓名"]: vb_str, "勝出": winner})
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=400)

# ======== Page: Match Trends ========
def page_trends(data):
    matches = data["matches"]
    if matches.empty:
        st.warning("無比賽數據")
        return

    if "賽事類型" in matches.columns:
        match_type = st.radio("賽事類型", ["全部", "例行賽", "季後賽"], horizontal=True)
        if match_type != "全部":
            matches = matches[matches["賽事類型"] == match_type]

    st.subheader("全隊技術指標月度趨勢")
    if "比賽日期" in matches.columns:
        m = matches.copy()
        m["年月"] = m["比賽日期"].dt.to_period("M").dt.to_timestamp()
        pct_cols = [f"{c}%" for c in STAT_COLUMNS if f"{c}%" in m.columns]
        monthly = m.groupby("年月")[pct_cols].mean().reset_index()
        if not monthly.empty:
            fig = px.line(monthly.melt(id_vars="年月", var_name="指標", value_name="效率%"), x="年月", y="效率%", color="指標", markers=True)
            st.plotly_chart(fig, use_container_width=True)

# ======== Page: ML Insights (保持原樣) ========
def page_ml_insights(data):
    st.subheader("🏅 MVP 綜合評分排行")
    mvp_path = PROCESSED_DIR / "mvp_rankings.csv"
    if mvp_path.exists():
        mvp = pd.read_csv(mvp_path)
        if not mvp.empty:
            name_col = "球員姓名" if "球員姓名" in mvp.columns else "姓名"
            top = mvp.nsmallest(15, "MVP_rank").copy()
            top["label"] = top.apply(lambda r: f"#{int(r.get('球員背號', 0))} {r[name_col]}", axis=1)
            fig = px.bar(top, y="label", x="MVP_score", orientation="h", color="球隊" if "球隊" in top.columns else None, color_discrete_map=TEAM_COLORS)
            fig.update_layout(yaxis=dict(autorange="reversed"), height=450)
            st.plotly_chart(fig, use_container_width=True)
    else: st.info("請執行 ML 步驟後查看")

# ======== Page: Roster & Career (保持原樣) ========
def page_roster_career():
    from analysis.career_tracking import load_rosters, get_player_career, get_player_transfers, get_veteran_players
    rosters = load_rosters()
    if not rosters: return
    st.subheader("🔍 球員生涯查詢")
    all_names = sorted({p["name"] for s in rosters.values() for t in s.values() for p in t})
    search_name = st.selectbox("選擇球員", all_names)
    if search_name:
        career = get_player_career(search_name)
        if career: st.dataframe(pd.DataFrame(career), hide_index=True, use_container_width=True)

# ======== Main ========
def main():
    inject_css()
    raw_data = load_data()
    if raw_data is None:
        st.error("⚠️ 找不到資料！")
        return

    # Sidebar
    st.sidebar.markdown("## 🏐 TVL 女子組儀表板")
    st.sidebar.markdown(f"*{SEASON} 賽季*")
    st.sidebar.divider()

    team_options = ["全聯盟"] + list(WOMEN_TEAMS.keys())
    team_filter = st.sidebar.selectbox("🏢 選擇隊伍", team_options)

    # 側邊欄動態摘要
    if team_filter != "全聯盟":
        color = TEAM_COLORS.get(team_filter, "#1B3A6B")
        st.sidebar.markdown(f'<div style="width:100%;height:4px;background:{color};border-radius:2px;margin:8px 0;"></div>', unsafe_allow_html=True)
        
        team_players = raw_data["players"][raw_data["players"]["球隊"] == team_filter]
        st.sidebar.markdown(f"### 📋 {team_filter} 快訊")
        if not team_players.empty:
            st.sidebar.write(f"🏃 球員人數: {len(team_players)} 人")
            st.sidebar.write(f"📏 平均身高: {team_players['身高(cm)'].mean():.1f} cm")
            captain = team_players[team_players.get("是否隊長", False) == True]
            if not captain.empty:
                st.sidebar.write(f"⭐ 隊長: {captain['姓名'].iloc[0]}")

    pos_options = ["全部位置"] + list(POS_COLORS.keys())
    pos_filter = st.sidebar.selectbox("🏃 篩選位置", pos_options)

    season_options = ["全部賽季"]
    if "季" in raw_data["summary"].columns:
        season_options += sorted(raw_data["summary"]["季"].dropna().unique().tolist(), reverse=True)
    season_filter = st.sidebar.selectbox("📅 選擇賽季", season_options, index=1 if len(season_options)>1 else 0)

    data = apply_filters(raw_data, team_filter, pos_filter, season_filter)

    # Tabs
    tab_names = ["📊 總覽", "🏃 球員分析", "⚔️ 球員比較", "📈 比賽趨勢", "🤖 ML 洞察", "📜 名單/生涯"]
    tabs = st.tabs(tab_names)
    with tabs[0]: page_overview(data, raw_data)
    with tabs[1]: page_player(data, raw_data)
    with tabs[2]: page_compare(data)
    with tabs[3]: page_trends(data)
    with tabs[4]: page_ml_insights(data)
    with tabs[5]: page_roster_career()

if __name__ == "__main__":
    main()