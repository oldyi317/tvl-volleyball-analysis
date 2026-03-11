"""
TVL 企業排球聯賽 — 女子組互動儀表板
啟動方式：streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

# 確保專案根目錄在 sys.path
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from config.settings import PROCESSED_DIR, MODELS_DIR, WOMEN_TEAMS, STAT_COLUMNS, SEASON

# ======== 頁面設定 ========
st.set_page_config(
    page_title="TVL 女子組數據儀表板",
    page_icon="🏐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ======== 隊伍配色 ========
TEAM_COLORS = {name: info["color"] for name, info in WOMEN_TEAMS.items()}
TEAM_ACCENTS = {name: info["accent"] for name, info in WOMEN_TEAMS.items()}
POS_COLORS = {
    "主攻手": "#E63946", "中間手": "#457B9D", "舉球員": "#2A9D8F",
    "自由球員": "#E9C46A", "副攻手": "#F4A261", "攻擊手": "#8338EC",
}


def _hex_to_rgba(hex_color: str, alpha: float = 0.2) -> str:
    """將 hex 色碼轉為 rgba 字串（Plotly 不支援 8 位 hex）"""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ======== 資料載入（快取） ========
@st.cache_data
def load_data():
    """載入清洗後的 CSV 資料"""
    data = {}

    p_path = PROCESSED_DIR / "players_clean.csv"
    m_path = PROCESSED_DIR / "matches_clean.csv"
    s_path = PROCESSED_DIR / "player_stats_summary.csv"

    if not p_path.exists():
        return None

    data["players"] = pd.read_csv(p_path)
    data["matches"] = pd.read_csv(m_path, parse_dates=["比賽日期"]) if m_path.exists() else pd.DataFrame()
    data["summary"] = pd.read_csv(s_path) if s_path.exists() else pd.DataFrame()

    # 確保球隊欄位存在
    for df_key in ["players", "matches", "summary"]:
        if "球隊" not in data[df_key].columns and not data[df_key].empty:
            data[df_key]["球隊"] = "未知"

    return data


# ======== 自訂 CSS ========
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap');
    html, body, [class*="st-"] { font-family: 'Noto Sans TC', 'Microsoft JhengHei', sans-serif; }
    .main .block-container { padding-top: 1.5rem; max-width: 1400px; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #0f1923 0%, #1a2d42 100%);
        border: 1px solid rgba(74,144,217,0.15);
        border-radius: 12px; padding: 16px 20px;
    }
    div[data-testid="stMetric"] label { color: #8899aa !important; font-size: 0.85rem; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #fff !important; font-weight: 800; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px; padding: 8px 20px;
        font-weight: 600; font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)


# ======== 頁面：總覽 ========
def page_overview(data, team_filter):
    players = data["players"]
    summary = data["summary"]

    if team_filter != "全聯盟":
        players = players[players["球隊"] == team_filter]
        summary = summary[summary.get("球隊", pd.Series(dtype=str)) == team_filter] if "球隊" in summary.columns else summary

    # 指標卡片
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

    # 兩欄圖表
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("得分排行")
        if not summary.empty and "得分" in summary.columns:
            name_col = "球員姓名" if "球員姓名" in summary.columns else "姓名"
            top10 = summary.nlargest(10, "得分").copy()
            top10["label"] = top10.apply(lambda r: f"#{int(r.get('球員背號', 0))} {r[name_col]}", axis=1)
            team_col = top10["球隊"] if "球隊" in top10.columns else "全隊"
            fig = px.bar(top10, y="label", x="得分", orientation="h",
                         color="球隊" if "球隊" in top10.columns else None,
                         color_discrete_map=TEAM_COLORS)
            fig.update_layout(yaxis=dict(autorange="reversed"), height=400,
                              margin=dict(l=0, r=20, t=10, b=0), showlegend=True)
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

    # 身高 vs 體重
    st.subheader("身高 vs 體重分佈")
    if "身高(cm)" in players.columns and "體重(kg)" in players.columns:
        fig = px.scatter(players, x="身高(cm)", y="體重(kg)",
                         color="位置" if "位置" in players.columns else None,
                         color_discrete_map=POS_COLORS,
                         symbol="球隊" if "球隊" in players.columns and team_filter == "全聯盟" else None,
                         hover_data=["姓名", "背號", "球隊"] if "球隊" in players.columns else ["姓名", "背號"],
                         size_max=15)
        fig.update_traces(marker=dict(size=12, line=dict(width=1, color="white")))
        fig.update_layout(height=450, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)


# ======== 頁面：球員分析 ========
def page_player(data, team_filter):
    players = data["players"]
    summary = data["summary"]

    if team_filter != "全聯盟":
        players = players[players["球隊"] == team_filter]

    if players.empty:
        st.warning("此隊伍沒有球員資料")
        return

    # 球員選擇
    player_options = {f"#{int(r['背號'])} {r['姓名']} ({r.get('球隊','')})": idx
                      for idx, r in players.iterrows()}
    selected_label = st.selectbox("選擇球員", list(player_options.keys()))
    p = players.loc[player_options[selected_label]]

    # 球員資訊卡
    col1, col2 = st.columns([2, 3])

    with col1:
        team_color = TEAM_COLORS.get(p.get("球隊", ""), "#1B3A6B")
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {team_color}22, {team_color}44);
                    border: 2px solid {team_color}; border-radius: 16px;
                    padding: 24px; text-align: center;">
            <div style="font-size: 48px; font-weight: 900; color: {team_color};">#{int(p.get('背號', 0))}</div>
            <div style="font-size: 28px; font-weight: 800; margin: 4px 0;">{p['姓名']}</div>
            <div style="font-size: 14px; color: #666; margin-bottom: 12px;">
                {p.get('球隊', '')} · {p.get('位置', '')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 身體數值
        body_cols = st.columns(2)
        for i, (label, key) in enumerate([
            ("身高", "身高(cm)"), ("體重", "體重(kg)"),
            ("攻擊高度", "攻擊高度(cm)"), ("攔網高度", "攔網高度(cm)"),
        ]):
            val = p.get(key, "-")
            if pd.notna(val) and val != "-":
                body_cols[i % 2].metric(label, f"{int(val)} cm" if "高" in label else f"{int(val)} {'cm' if 'cm' in key else 'kg'}")

        if pd.notna(p.get("MBTI")):
            st.metric("MBTI", p["MBTI"])

    with col2:
        # 雷達圖
        pid = p.get("player_id", p.name)
        player_summary = summary[summary["player_id"] == pid] if "player_id" in summary.columns else pd.DataFrame()

        if not player_summary.empty:
            ps = player_summary.iloc[0]
            labels = []
            values = []
            avg_values = []
            for col in STAT_COLUMNS:
                pct = f"{col}%"
                if pct in ps.index and pd.notna(ps[pct]):
                    labels.append(col)
                    values.append(float(ps[pct]))
                    avg_values.append(float(summary[pct].mean()) if pct in summary.columns else 0)

            if len(labels) >= 3:
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=labels + [labels[0]],
                    fill="toself", name=p["姓名"],
                    line=dict(color=team_color, width=2), fillcolor=_hex_to_rgba(team_color)))
                fig.add_trace(go.Scatterpolar(r=avg_values + [avg_values[0]], theta=labels + [labels[0]],
                    name="全聯盟平均", line=dict(color="gray", dash="dash", width=1.5)))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True)),
                                  height=400, margin=dict(l=60, r=60, t=40, b=40),
                                  legend=dict(x=0.85, y=1.1))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("此球員尚無賽季彙總數據")


# ======== 頁面：球員比較 ========
def page_compare(data, team_filter):
    players = data["players"]
    summary = data["summary"]

    if players.empty or summary.empty:
        st.warning("資料不足，無法比較")
        return

    col1, col2 = st.columns(2)
    player_opts = {f"#{int(r['背號'])} {r['姓名']} ({r.get('球隊','')})": r.get("player_id", idx)
                   for idx, r in players.iterrows()}
    opts_list = list(player_opts.keys())

    with col1:
        label_a = st.selectbox("球員 A", opts_list, index=0)
    with col2:
        default_b = min(1, len(opts_list) - 1)
        label_b = st.selectbox("球員 B", opts_list, index=default_b)

    pid_a, pid_b = player_opts[label_a], player_opts[label_b]

    sa = summary[summary["player_id"] == pid_a]
    sb = summary[summary["player_id"] == pid_b]

    if sa.empty or sb.empty:
        st.warning("所選球員缺少數據")
        return

    sa, sb = sa.iloc[0], sb.iloc[0]
    pa = players[players["player_id"] == pid_a].iloc[0] if "player_id" in players.columns else players.iloc[0]
    pb = players[players["player_id"] == pid_b].iloc[0] if "player_id" in players.columns else players.iloc[1]

    col_radar, col_table = st.columns([1, 1])

    with col_radar:
        st.subheader("技術指標比較")
        labels, vals_a, vals_b = [], [], []
        for col in STAT_COLUMNS:
            pct = f"{col}%"
            if pct in sa.index and pd.notna(sa[pct]) and pct in sb.index and pd.notna(sb[pct]):
                labels.append(col)
                vals_a.append(float(sa[pct]))
                vals_b.append(float(sb[pct]))

        if len(labels) >= 3:
            fig = go.Figure()
            color_a = TEAM_COLORS.get(pa.get("球隊", ""), "#1B3A6B")
            color_b = TEAM_COLORS.get(pb.get("球隊", ""), "#D4213D")
            fig.add_trace(go.Scatterpolar(r=vals_a + [vals_a[0]], theta=labels + [labels[0]],
                fill="toself", name=pa["姓名"],
                line=dict(color=color_a, width=2), fillcolor=_hex_to_rgba(color_a)))
            fig.add_trace(go.Scatterpolar(r=vals_b + [vals_b[0]], theta=labels + [labels[0]],
                fill="toself", name=pb["姓名"],
                line=dict(color=color_b, width=2), fillcolor=_hex_to_rgba(color_b)))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True)),
                              height=420, margin=dict(l=60, r=60, t=40, b=40))
            st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.subheader("數據對比")
        rows = []
        for col in STAT_COLUMNS:
            pct = f"{col}%"
            if pct in sa.index:
                va, vb = sa.get(pct, 0), sb.get(pct, 0)
                rows.append({"指標": f"{col}效率", pa["姓名"]: f"{va:.1f}%", pb["姓名"]: f"{vb:.1f}%",
                             "勝出": pa["姓名"] if va > vb else (pb["姓名"] if vb > va else "平手")})
        if "得分" in sa.index:
            va, vb = int(sa.get("得分", 0)), int(sb.get("得分", 0))
            rows.append({"指標": "總得分", pa["姓名"]: str(va), pb["姓名"]: str(vb),
                         "勝出": pa["姓名"] if va > vb else (pb["姓名"] if vb > va else "平手")})

        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


# ======== 頁面：比賽趨勢 ========
def page_trends(data, team_filter):
    matches = data["matches"]

    if matches.empty:
        st.warning("無比賽數據")
        return

    if team_filter != "全聯盟" and "球隊" in matches.columns:
        matches = matches[matches["球隊"] == team_filter]

    # 月度趨勢
    st.subheader("全隊技術指標月度趨勢")
    if "比賽日期" in matches.columns:
        matches = matches.copy()
        matches["年月"] = matches["比賽日期"].dt.to_period("M").dt.to_timestamp()
        pct_cols = [f"{c}%" for c in STAT_COLUMNS if f"{c}%" in matches.columns]
        monthly = matches.groupby("年月")[pct_cols].mean().reset_index()

        if not monthly.empty:
            fig = px.line(monthly.melt(id_vars="年月", var_name="指標", value_name="效率%"),
                          x="年月", y="效率%", color="指標", markers=True)
            fig.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    # 對手比較
    st.subheader("對不同對手的表現")
    if "對手" in matches.columns:
        pct_cols = [f"{c}%" for c in ["攻擊", "防守", "接發球"] if f"{c}%" in matches.columns]
        if pct_cols:
            opp_stats = matches.groupby("對手")[pct_cols].mean().reset_index()
            fig = px.bar(opp_stats.melt(id_vars="對手", var_name="指標", value_name="效率%"),
                         x="對手", y="效率%", color="指標", barmode="group")
            fig.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)


# ======== 頁面：跨隊比較 ========
def page_cross_team(data):
    players = data["players"]
    summary = data["summary"]

    if "球隊" not in players.columns:
        st.warning("資料中缺少球隊欄位")
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
            fig.update_layout(yaxis=dict(autorange="reversed"), height=500,
                              margin=dict(l=0, r=20, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)


# ======== Page: ML Insights ========
def page_ml_insights(data, team_filter):
    matches = data["matches"]

    # --- MVP Rankings ---
    st.subheader("🏅 MVP 綜合評分排行")
    mvp_path = PROCESSED_DIR / "mvp_rankings.csv"
    if mvp_path.exists():
        mvp = pd.read_csv(mvp_path)
        if team_filter != "全聯盟" and "球隊" in mvp.columns:
            mvp = mvp[mvp["球隊"] == team_filter]

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
                                  margin=dict(l=0, r=20, t=10, b=0),
                                  xaxis_title="MVP Score (0-100)")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown("**MVP 評分公式**")
                st.markdown("""
                各項指標經 Z-score 標準化後加權計算：
                - 攻擊效率：25%
                - 攔網效率：15%
                - 發球效率：15%
                - 接發球效率：15%
                - 防守效率：15%
                - 總得分：10%
                - 舉球效率：5%
                """)
    else:
        st.info("尚無 MVP 數據，請先執行：`python main.py --steps ml`")

    st.divider()

    # --- Anomaly Detection ---
    st.subheader("🔍 異常表現偵測")
    anomaly_path = PROCESSED_DIR / "anomalies.csv"
    if anomaly_path.exists():
        anomalies = pd.read_csv(anomaly_path, parse_dates=["比賽日期"])
        if team_filter != "全聯盟" and "球隊" in anomalies.columns:
            anomalies = anomalies[anomalies["球隊"] == team_filter]

        if not anomalies.empty:
            name_col = "球員姓名" if "球員姓名" in anomalies.columns else "姓名"

            col_exc, col_und = st.columns(2)

            with col_exc:
                st.markdown("#### ⭐ 超常發揮")
                exc = anomalies[anomalies["anomaly_type"] == "exceptional"].nlargest(10, "max_z")
                if not exc.empty:
                    display = exc[[name_col, "對手", "比賽日期", "max_z"]].copy()
                    display.columns = ["球員", "對手", "日期", "異常程度 (z)"]
                    display["異常程度 (z)"] = display["異常程度 (z)"].round(2)
                    if "球隊" in exc.columns:
                        display.insert(1, "球隊", exc["球隊"].values)
                    st.dataframe(display, hide_index=True, use_container_width=True)
                else:
                    st.caption("無超常發揮紀錄")

            with col_und:
                st.markdown("#### ⚠️ 低於水準")
                und = anomalies[anomalies["anomaly_type"] == "underperform"].nlargest(10, "max_z")
                if not und.empty:
                    display = und[[name_col, "對手", "比賽日期", "max_z"]].copy()
                    display.columns = ["球員", "對手", "日期", "異常程度 (z)"]
                    display["異常程度 (z)"] = display["異常程度 (z)"].round(2)
                    if "球隊" in und.columns:
                        display.insert(1, "球隊", und["球隊"].values)
                    st.dataframe(display, hide_index=True, use_container_width=True)
                else:
                    st.caption("無低於水準紀錄")

            # Anomaly scatter
            st.markdown("#### 異常表現分佈")
            if "得分" in anomalies.columns and "max_z" in anomalies.columns:
                anomalies["label"] = anomalies.apply(
                    lambda r: f"{r.get(name_col, '?')} vs {r.get('對手', '?')}", axis=1)
                fig = px.scatter(anomalies, x="比賽日期", y="max_z",
                                 color="anomaly_type",
                                 color_discrete_map={"exceptional": "#2ECC71", "underperform": "#E74C3C"},
                                 hover_data=["label", "得分"],
                                 size="max_z", size_max=15)
                fig.add_hline(y=2.0, line_dash="dash", line_color="gray",
                              annotation_text="z=2.0 threshold")
                fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0),
                                  yaxis_title="異常程度 (|z-score|)")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("尚無異常偵測數據，請先執行：`python main.py --steps ml`")

    st.divider()

    # --- Model Performance ---
    st.subheader("🤖 預測模型資訊")
    model_files = {
        "得分預測": "score_predictor.joblib",
        "攻擊效率預測": "attack_predictor.joblib",
        "防守效率預測": "defense_predictor.joblib",
    }

    cols = st.columns(len(model_files))
    for i, (label, filename) in enumerate(model_files.items()):
        path = MODELS_DIR / filename
        with cols[i]:
            if path.exists():
                bundle = __import__("joblib").load(path)
                model_name = bundle.get("model_name", type(bundle["model"]).__name__)
                st.metric(label, model_name)
                st.caption(f"Features: {len(bundle['feature_cols'])}")
            else:
                st.metric(label, "未訓練")


# ======== 主程式 ========
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

    st.sidebar.divider()
    st.sidebar.markdown("📊 資料來源：[TVL 官網](https://tvl.ctvba.org.tw/)")
    st.sidebar.markdown("🔄 重新爬取：`python main.py`")

    # 載入資料
    data = load_data()
    if data is None:
        st.error("⚠️ 找不到資料！請先執行爬蟲與清洗：")
        st.code("python main.py --steps scrape clean", language="bash")
        return

    # 頁籤
    tab_names = ["📊 總覽", "🏃 球員分析", "⚔️ 球員比較", "📈 比賽趨勢", "🤖 ML 洞察"]
    if team_filter == "全聯盟":
        tab_names.append("🏆 跨隊比較")

    tabs = st.tabs(tab_names)

    with tabs[0]:
        page_overview(data, team_filter)
    with tabs[1]:
        page_player(data, team_filter)
    with tabs[2]:
        page_compare(data, team_filter)
    with tabs[3]:
        page_trends(data, team_filter)
    with tabs[4]:
        page_ml_insights(data, team_filter)
    if team_filter == "全聯盟" and len(tabs) > 5:
        with tabs[5]:
            page_cross_team(data)


if __name__ == "__main__":
    main()
