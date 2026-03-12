"""
TVL 企業排球聯賽 — 女子組互動儀表板 v2
Fixes: team colors, radar visibility, NaN handling, position filter, layout
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

    # Ensure team column exists everywhere
    for df in [players, matches, summary]:
        if not df.empty and "球隊" not in df.columns:
            df["球隊"] = "未知"

    # If summary still has "未知", try merging from players
    if not summary.empty and "player_id" in summary.columns and "player_id" in players.columns:
        if summary["球隊"].eq("未知").all() or summary["球隊"].isna().all():
            team_map = players.set_index("player_id")["球隊"].to_dict()
            summary["球隊"] = summary["player_id"].map(team_map).fillna("未知")

    # Also merge position into summary if missing
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
    """Apply team, position, and season filters to all dataframes."""
    players = data["players"].copy()
    matches = data["matches"].copy()
    summary = data["summary"].copy()

    # Season filter (applies to matches and summary)
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
def page_overview(data):
    players, summary = data["players"], data["summary"]

    # Stat cards
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

    # Scatter - simplified: color by position only, symbol by team
    st.subheader("身高 vs 體重分佈")
    if "身高(cm)" in players.columns and "體重(kg)" in players.columns:
        fig = px.scatter(players, x="身高(cm)", y="體重(kg)",
                         color="位置" if "位置" in players.columns else None,
                         color_discrete_map=POS_COLORS,
                         hover_data=["姓名", "背號", "球隊"],
                         text="姓名" if len(players) <= 30 else None)
        fig.update_traces(marker=dict(size=12, line=dict(width=1, color="white")),
                          textposition="top center", textfont=dict(size=9))
        fig.update_layout(height=450, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)


# ======== Page: Player Analysis ========
def page_player(data):
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
        # Player card
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
        # Radar chart - FIXED: brighter colors, thicker lines
        pid = p.get("player_id", p.name)
        player_summary = summary[summary["player_id"] == pid] if "player_id" in summary.columns else pd.DataFrame()

        if not player_summary.empty:
            ps = player_summary.iloc[0]
            labels, values, avg_values = [], [], []
            for col in STAT_COLUMNS:
                pct = f"{col}%"
                if pct in ps.index and pd.notna(ps[pct]):
                    labels.append(col)
                    values.append(float(ps[pct]))
                    avg_values.append(float(summary[pct].mean()) if pct in summary.columns else 0)

            if len(labels) >= 3:
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=values + [values[0]], theta=labels + [labels[0]],
                    fill="toself", name=p["姓名"],
                    line=dict(color=team_color, width=3),
                    fillcolor=_hex_to_rgba(team_color, 0.3),
                    marker=dict(size=6)))
                fig.add_trace(go.Scatterpolar(
                    r=avg_values + [avg_values[0]], theta=labels + [labels[0]],
                    name="全聯盟平均",
                    line=dict(color="#AAAAAA", dash="dash", width=2),
                    marker=dict(size=4)))
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, gridcolor="rgba(150,150,150,0.3)"),
                        angularaxis=dict(gridcolor="rgba(150,150,150,0.3)")),
                    height=420, margin=dict(l=60, r=60, t=40, b=40),
                    legend=dict(x=0.8, y=1.1), font=dict(size=13))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("此球員尚無賽季彙總數據")


# ======== Page: Player Compare ========
def page_compare(data):
    players, summary = data["players"], data["summary"]
    if players.empty or summary.empty:
        st.warning("資料不足")
        return

    col1, col2 = st.columns(2)
    player_opts = {f"#{int(r['背號'])} {r['姓名']} ({r.get('球隊','')})": r.get("player_id", idx)
                   for idx, r in players.iterrows()}
    opts_list = list(player_opts.keys())

    with col1:
        label_a = st.selectbox("球員 A", opts_list, index=0)
    with col2:
        label_b = st.selectbox("球員 B", opts_list, index=min(1, len(opts_list) - 1))

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
        st.subheader("技術指標比較")
        labels, vals_a, vals_b = [], [], []
        for col in STAT_COLUMNS:
            pct = f"{col}%"
            va = sa.get(pct, None)
            vb = sb.get(pct, None)
            if pd.notna(va) and pd.notna(vb):
                labels.append(col)
                vals_a.append(float(va))
                vals_b.append(float(vb))

        if len(labels) >= 3:
            color_a = TEAM_COLORS.get(pa.get("球隊", ""), "#4A90D9")
            color_b = TEAM_COLORS.get(pb.get("球隊", ""), "#E65100")
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=vals_a + [vals_a[0]], theta=labels + [labels[0]],
                fill="toself", name=pa["姓名"],
                line=dict(color=color_a, width=3),
                fillcolor=_hex_to_rgba(color_a, 0.25), marker=dict(size=6)))
            fig.add_trace(go.Scatterpolar(
                r=vals_b + [vals_b[0]], theta=labels + [labels[0]],
                fill="toself", name=pb["姓名"],
                line=dict(color=color_b, width=3),
                fillcolor=_hex_to_rgba(color_b, 0.2), marker=dict(size=6)))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, gridcolor="rgba(150,150,150,0.3)"),
                    angularaxis=dict(gridcolor="rgba(150,150,150,0.3)")),
                height=420, margin=dict(l=60, r=60, t=40, b=40), font=dict(size=13))
            st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.subheader("數據對比")
        rows = []
        for col in STAT_COLUMNS:
            pct = f"{col}%"
            va = sa.get(pct, None)
            vb = sb.get(pct, None)
            # FIXED: handle NaN - show "-" instead of "nan%"
            va_str = f"{va:.1f}%" if pd.notna(va) else "-"
            vb_str = f"{vb:.1f}%" if pd.notna(vb) else "-"
            if pd.notna(va) and pd.notna(vb):
                winner = pa["姓名"] if va > vb else (pb["姓名"] if vb > va else "平手")
            else:
                winner = "-"
            rows.append({"指標": f"{col}效率", pa["姓名"]: va_str, pb["姓名"]: vb_str, "勝出": winner})

        if "得分" in sa.index:
            va, vb = sa.get("得分", 0), sb.get("得分", 0)
            va = int(va) if pd.notna(va) else 0
            vb = int(vb) if pd.notna(vb) else 0
            rows.append({"指標": "總得分", pa["姓名"]: str(va), pb["姓名"]: str(vb),
                         "勝出": pa["姓名"] if va > vb else (pb["姓名"] if vb > va else "平手")})

        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=420)


# ======== Page: Match Trends ========
def page_trends(data):
    matches = data["matches"]
    if matches.empty:
        st.warning("無比賽數據")
        return

    # Match type filter
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
            fig = px.line(monthly.melt(id_vars="年月", var_name="指標", value_name="效率%"),
                          x="年月", y="效率%", color="指標", markers=True)
            fig.update_traces(line=dict(width=2.5), marker=dict(size=6))
            fig.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("對不同對手的表現")
    if "對手" in matches.columns:
        # Exclude playoff-tagged opponents for cleaner comparison
        opp_matches = matches[~matches["對手"].str.contains("|".join(PLAYOFF_TAGS), na=False)] if "賽事類型" not in matches.columns else matches
        pct_cols = [f"{c}%" for c in ["攻擊", "防守", "接發球"] if f"{c}%" in opp_matches.columns]
        if pct_cols:
            opp_stats = opp_matches.groupby("對手")[pct_cols].mean().reset_index()
            # Sort by number of matches
            opp_count = opp_matches.groupby("對手").size().reset_index(name="場次")
            opp_stats = opp_stats.merge(opp_count, on="對手")
            opp_stats.sort_values("場次", ascending=False, inplace=True)

            fig = px.bar(opp_stats.melt(id_vars=["對手", "場次"], var_name="指標", value_name="效率%"),
                         x="對手", y="效率%", color="指標", barmode="group",
                         color_discrete_sequence=["#457B9D", "#2A9D8F", "#E63946"],
                         hover_data=["場次"])
            fig.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)


# ======== Page: ML Insights ========
def page_ml_insights(data):
    st.subheader("🏅 MVP 綜合評分排行")
    mvp_path = PROCESSED_DIR / "mvp_rankings.csv"
    if mvp_path.exists():
        mvp = pd.read_csv(mvp_path)

        # Filter by season if season column in sidebar-filtered data
        if not data["summary"].empty and "季" in data["summary"].columns:
            active_seasons = data["summary"]["季"].unique()
            if "季" in mvp.columns:
                mvp = mvp[mvp["季"].isin(active_seasons)]
        if not mvp.empty:
            name_col = "球員姓名" if "球員姓名" in mvp.columns else "姓名"
            top = mvp.nsmallest(15, "MVP_rank").copy()
            top["label"] = top.apply(lambda r: f"#{int(r.get('球員背號', 0))} {r[name_col]}", axis=1)

            col1, col2 = st.columns([2, 1])
            with col1:
                fig = px.bar(top, y="label", x="MVP_score", orientation="h",
                             color="球隊" if "球隊" in top.columns else None,
                             color_discrete_map=TEAM_COLORS)
                fig.update_layout(yaxis=dict(autorange="reversed"), height=450,
                                  margin=dict(l=0, r=20, t=10, b=0), xaxis_title="MVP Score (0-100)")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown("""**MVP 評分公式**

各項指標經 Z-score 標準化後加權：
- 攻擊效率：25%
- 攔網效率：15%
- 發球效率：15%
- 接發球效率：15%
- 防守效率：15%
- 總得分：10%
- 舉球效率：5%""")
    else:
        st.info("請先執行 `python main.py --steps ml`")

    st.divider()

    st.subheader("🔍 異常表現偵測")
    anomaly_path = PROCESSED_DIR / "anomalies.csv"
    if anomaly_path.exists():
        anomalies = pd.read_csv(anomaly_path, parse_dates=["比賽日期"])
        # Filter by active seasons
        if not data["summary"].empty and "季" in data["summary"].columns:
            active_seasons = data["summary"]["季"].unique()
            if "季" in anomalies.columns:
                anomalies = anomalies[anomalies["季"].isin(active_seasons)]
        if not anomalies.empty:
            name_col = "球員姓名" if "球員姓名" in anomalies.columns else "姓名"
            col_exc, col_und = st.columns(2)
            with col_exc:
                st.markdown("#### ⭐ 超常發揮")
                exc = anomalies[anomalies["anomaly_type"] == "exceptional"].nlargest(10, "max_z")
                if not exc.empty:
                    d = exc[[name_col, "球隊", "對手", "比賽日期", "max_z"]].copy() if "球隊" in exc.columns else exc[[name_col, "對手", "比賽日期", "max_z"]].copy()
                    d.columns = [*d.columns[:-1], "z-score"]
                    d["z-score"] = d["z-score"].round(2)
                    st.dataframe(d, hide_index=True, use_container_width=True)
            with col_und:
                st.markdown("#### ⚠️ 低於水準")
                und = anomalies[anomalies["anomaly_type"] == "underperform"].nlargest(10, "max_z")
                if not und.empty:
                    d = und[[name_col, "球隊", "對手", "比賽日期", "max_z"]].copy() if "球隊" in und.columns else und[[name_col, "對手", "比賽日期", "max_z"]].copy()
                    d.columns = [*d.columns[:-1], "z-score"]
                    d["z-score"] = d["z-score"].round(2)
                    st.dataframe(d, hide_index=True, use_container_width=True)

            if "max_z" in anomalies.columns:
                st.markdown("#### 異常表現時間分佈")
                anomalies["label"] = anomalies.apply(lambda r: f"{r.get(name_col, '?')} vs {r.get('對手', '?')}", axis=1)
                fig = px.scatter(anomalies, x="比賽日期", y="max_z",
                                 color="anomaly_type",
                                 color_discrete_map={"exceptional": "#2ECC71", "underperform": "#E74C3C"},
                                 hover_data=["label"], size="max_z", size_max=15)
                fig.add_hline(y=2.0, line_dash="dash", line_color="gray", annotation_text="z=2.0")
                fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="|z-score|")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("請先執行 `python main.py --steps ml`")

    st.divider()
    st.subheader("🤖 預測模型")
    model_files = {"得分預測": "score_predictor.joblib", "攻擊效率": "attack_predictor.joblib", "防守效率": "defense_predictor.joblib"}
    cols = st.columns(len(model_files))
    for i, (label, fn) in enumerate(model_files.items()):
        path = MODELS_DIR / fn
        with cols[i]:
            if path.exists():
                import joblib
                bundle = joblib.load(path)
                st.metric(label, bundle.get("model_name", type(bundle["model"]).__name__))
                st.caption(f"{len(bundle['feature_cols'])} features")
            else:
                st.metric(label, "未訓練")


# ======== Page: Cross-team Compare ========
def page_cross_team(data):
    players, summary = data["players"], data["summary"]

    if "球隊" not in players.columns:
        st.warning("缺少球隊欄位")
        return

    st.subheader("各隊平均身體素質")
    body_cols = [c for c in ["身高(cm)", "體重(kg)", "年齡"] if c in players.columns]
    if body_cols:
        team_body = players.groupby("球隊")[body_cols].mean().round(1).reset_index()
        fig = px.bar(team_body.melt(id_vars="球隊", var_name="指標", value_name="數值"),
                     x="球隊", y="數值", color="指標", barmode="group",
                     color_discrete_sequence=["#457B9D", "#E63946", "#2A9D8F"])
        fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    if not summary.empty and "球隊" in summary.columns:
        st.subheader("各隊技術指標平均")
        pct_cols = [f"{c}%" for c in STAT_COLUMNS if f"{c}%" in summary.columns]
        if pct_cols:
            team_stats = summary.groupby("球隊")[pct_cols].mean().round(1).reset_index()
            fig = px.bar(team_stats.melt(id_vars="球隊", var_name="指標", value_name="效率%"),
                         x="指標", y="效率%", color="球隊", barmode="group",
                         color_discrete_map=TEAM_COLORS)
            fig.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("全聯盟得分排行 Top 15")
        if "得分" in summary.columns:
            name_col = "球員姓名" if "球員姓名" in summary.columns else "姓名"
            top = summary.nlargest(15, "得分").copy()
            top["label"] = top.apply(lambda r: f"#{int(r.get('球員背號', 0))} {r[name_col]}", axis=1)
            fig = px.bar(top, y="label", x="得分", orientation="h",
                         color="球隊", color_discrete_map=TEAM_COLORS)
            fig.update_layout(yaxis=dict(autorange="reversed"), height=500, margin=dict(l=0, r=20, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)


# ======== Page: Roster & Career ========
def page_roster_career():
    from analysis.career_tracking import (
        load_rosters, get_player_transfers, get_veteran_players,
        get_season_roster, get_all_seasons, get_player_career,
    )

    rosters = load_rosters()
    if not rosters:
        st.info("No historical roster data found (data/rosters.json)")
        return

    all_seasons = get_all_seasons()

    # --- Season Rosters ---
    st.subheader("📋 各賽季名單")
    col1, col2 = st.columns(2)
    with col1:
        sel_season = st.selectbox("賽季", all_seasons, index=len(all_seasons)-1, key="roster_season")
    with col2:
        teams_in_season = list(rosters.get(sel_season, {}).keys())
        sel_team = st.selectbox("球隊", teams_in_season, key="roster_team") if teams_in_season else None

    if sel_team:
        roster = get_season_roster(sel_season, sel_team)
        if roster:
            roster_df = pd.DataFrame(roster)
            roster_df = roster_df.rename(columns={"num": "背號", "name": "姓名", "pos": "位置"})
            # Add markers
            if "captain" in roster_df.columns:
                roster_df["姓名"] = roster_df.apply(
                    lambda r: f"⭐ {r['姓名']}" if r.get("captain") else r["姓名"], axis=1)
            if "foreign" in roster_df.columns:
                roster_df["姓名"] = roster_df.apply(
                    lambda r: f"{r['姓名']} 🌍" if r.get("foreign") else r["姓名"], axis=1)
            display_cols = ["背號", "姓名", "位置"]
            st.dataframe(roster_df[display_cols].sort_values("背號"),
                         hide_index=True, use_container_width=True)
            st.caption("⭐ = 隊長，🌍 = 外援")

    st.divider()

    # --- Player Career Search ---
    st.subheader("🔍 球員生涯查詢")
    # Build all player names from all seasons
    all_names = set()
    for season_teams in rosters.values():
        for players in season_teams.values():
            for p in players:
                all_names.add(p["name"])
    all_names = sorted(all_names)

    search_name = st.selectbox("選擇球員", all_names, key="career_search")
    if search_name:
        career = get_player_career(search_name)
        if career:
            career_df = pd.DataFrame(career)
            career_df = career_df.rename(columns={
                "season": "賽季", "team_original": "當時隊名",
                "team_current": "現隊名", "num": "背號", "pos": "位置",
            })
            display = career_df[["賽季", "當時隊名", "背號", "位置"]].copy()
            display["隊長"] = career_df.get("captain", False).apply(lambda x: "✅" if x else "")
            st.dataframe(display, hide_index=True, use_container_width=True)

            # Visual timeline
            if len(career) > 1:
                teams_over_time = career_df[["賽季", "當時隊名"]].drop_duplicates()
                fig = px.scatter(teams_over_time, x="賽季", y="當時隊名",
                                 size=[20]*len(teams_over_time),
                                 color="當時隊名", color_discrete_map=TEAM_COLORS)
                fig.update_traces(marker=dict(size=20))
                fig.update_layout(height=200, margin=dict(l=0, r=0, t=10, b=0),
                                  showlegend=False, yaxis_title="")
                st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- Transfers ---
    st.subheader("🔄 球員流動紀錄")
    transfers = get_player_transfers()
    if transfers:
        t_df = pd.DataFrame(transfers)
        t_df = t_df.rename(columns={
            "name": "球員", "from_team": "原球隊", "from_season": "原賽季",
            "to_team": "新球隊", "to_season": "轉入賽季",
        })
        st.dataframe(t_df, hide_index=True, use_container_width=True)
    else:
        st.caption("無轉隊紀錄")

    st.divider()

    # --- Veterans ---
    st.subheader("🏅 資深球員（出賽 3 季以上）")
    veterans = get_veteran_players(min_seasons=3)
    if veterans:
        v_df = pd.DataFrame(veterans)
        v_df = v_df.rename(columns={
            "name": "球員", "seasons_played": "出賽季數",
            "latest_team": "最近球隊", "latest_pos": "位置",
        })
        v_df["賽季"] = v_df["seasons"].apply(lambda x: ", ".join(x))
        st.dataframe(v_df[["球員", "出賽季數", "最近球隊", "位置", "賽季"]],
                     hide_index=True, use_container_width=True)


# ======== Main ========
def main():
    inject_css()

    # Sidebar
    st.sidebar.markdown("## 🏐 TVL 女子組儀表板")
    st.sidebar.markdown(f"*{SEASON} 賽季*")
    st.sidebar.divider()

    team_options = ["全聯盟"] + list(WOMEN_TEAMS.keys())
    team_filter = st.sidebar.selectbox("🏢 選擇隊伍", team_options)

    if team_filter != "全聯盟":
        color = TEAM_COLORS.get(team_filter, "#1B3A6B")
        st.sidebar.markdown(f'<div style="width:100%;height:4px;background:{color};border-radius:2px;margin:8px 0;"></div>',
                            unsafe_allow_html=True)

    # Position filter
    pos_options = ["全部位置"] + list(POS_COLORS.keys())
    pos_filter = st.sidebar.selectbox("🏃 篩選位置", pos_options)

    # Season filter
    raw_data = load_data()
    if raw_data is None:
        st.error("⚠️ 找不到資料！請先執行：`python main.py --steps scrape clean`")
        return

    season_options = ["全部賽季"]
    if "季" in raw_data["summary"].columns:
        seasons = sorted(raw_data["summary"]["季"].dropna().unique().tolist(), reverse=True)
        season_options += seasons
    elif "季" in raw_data["matches"].columns:
        seasons = sorted(raw_data["matches"]["季"].dropna().unique().tolist(), reverse=True)
        season_options += seasons

    # Default to latest season (index 1) if available
    default_idx = 1 if len(season_options) > 1 else 0
    season_filter = st.sidebar.selectbox("📅 選擇賽季", season_options, index=default_idx)

    st.sidebar.divider()
    st.sidebar.markdown("📊 [TVL 官網](https://tvl.ctvba.org.tw/)")
    st.sidebar.markdown("🔄 `python main.py`")

    data = apply_filters(raw_data, team_filter, pos_filter, season_filter)

    # Tabs
    tab_names = ["📊 總覽", "🏃 球員分析", "⚔️ 球員比較", "📈 比賽趨勢", "🤖 ML 洞察", "📜 名單/生涯"]
    if team_filter == "全聯盟" and pos_filter == "全部位置":
        tab_names.append("🏆 跨隊比較")

    tabs = st.tabs(tab_names)
    with tabs[0]: page_overview(data)
    with tabs[1]: page_player(data)
    with tabs[2]: page_compare(data)
    with tabs[3]: page_trends(data)
    with tabs[4]: page_ml_insights(data)
    with tabs[5]: page_roster_career()
    if len(tabs) > 6:
        with tabs[6]:
            cross_data = apply_filters(raw_data, "全聯盟", "全部位置", season_filter)
            page_cross_team(cross_data)


if __name__ == "__main__":
    main()
