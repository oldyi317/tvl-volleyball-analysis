"""
TVL 企業排球聯賽 — 女子組互動儀表板 v6 (高對比白色主題版)
優化內容：
1. 雷達圖背景改為白色，大幅提升閱讀性
2. 文字與格線顏色改為深色，確保對比清晰
3. 保留之前的資料清洗與同隊比較變色邏輯
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

# ======== 顏色設定 ========
TEAM_COLORS = {name: info["color"] for name, info in WOMEN_TEAMS.items()}
POS_COLORS = {"主攻手": "#E63946", "中間手": "#457B9D", "舉球員": "#2A9D8F",
              "自由球員": "#E9C46A", "副攻手": "#F4A261"}

# v6 修改：雷達圖改為白色主題
RADAR_BG_COLOR = "#FFFFFF"         # 背景改為白色
LEAGUE_AVG_COLOR = "#999999"       # 聯盟平均改為深灰色 (在白底較清楚)
POS_AVG_COLOR = "#FF8C00"          # 位置平均 (深橘色)
COMPARE_COLOR_A = "rgb(0, 191, 255)" # 同隊比較A (維持亮藍)
COMPARE_COLOR_B = "rgb(50, 205, 50)" # 同隊比較B (維持亮綠)
TEXT_COLOR_DARK = "#2C3E50"        # 深色文字

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

    # 資料清洗：統一位置名稱
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
    html, body, [class*="st-"] { font-family: 'Noto Sans TC', sans-serif; font-size: 18px; color: #2C3E50; }
    
    /* Metric 卡片維持深色背景，與白色圖表形成對比 */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a2a3a 0%, #0f1923 100%);
        border: 2px solid rgba(74,144,217,0.3); border-radius: 15px;
        padding: 20px !important; color: white;
    }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 800 !important; }
    div[data-testid="stMetricLabel"] { color: #a0aec0 !important; }

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

# ======== v6 修改：雷達圖共用設定 (白色主題) ========
def get_radar_layout():
    return dict(
        polar=dict(
            bgcolor=RADAR_BG_COLOR, # 白色背景
            radialaxis=dict(
                visible=True, range=[0, 100], tickfont_size=14,
                gridcolor="#E0E0E0", linecolor="#E0E0E0", # 淺灰色格線
                tickfont=dict(color=TEXT_COLOR_DARK) # 深色刻度文字
            ),
            angularaxis=dict(
                tickfont=dict(size=18, weight="bold", color=TEXT_COLOR_DARK), # 深色外圈文字
                gridcolor="#E0E0E0", linecolor="#E0E0E0"
            )
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_COLOR_DARK, size=16), # 整體深色文字
        height=550,
        legend=dict(font_size=16, orientation="h", y=-0.15, x=0.5, xanchor="center", bgcolor="rgba(255,255,255,0.8)", bordercolor="#E0E0E0", borderwidth=1)
    )

# ======== 分頁: 球員分析 ========
def page_player(data, raw_data):
    p, s = data["players"], data["summary"]
    if p.empty: return st.warning("無符合條件球員")
    opts = {f"#{int(r['背號'])} {r['姓名']} ({r.get('球隊','')})": idx for idx, r in p.iterrows()}
    player = p.loc[opts[st.selectbox("🔍 選擇球員", list(opts.keys()))]]
    t_color = TEAM_COLORS.get(player.get("球隊", ""), "#4A90D9")

    c1, c2 = st.columns([1, 1.5])
    with c1:
        # 球員卡維持深色背景，突出顯示
        st.markdown(f'<div style="background: linear-gradient(135deg, {t_color}33, {t_color}66); border: 3px solid {t_color}; border-radius: 20px; padding: 40px; text-align: center;"><div style="font-size: 80px; font-weight: 900; color: {t_color};">#{int(player.get("背號", 0))}</div><div style="font-size: 45px; font-weight: 800; color: {TEXT_COLOR_DARK};">{player["姓名"]}</div><div style="font-size: 22px; color: #666;">{player.get("球隊", "")} | {player.get("位置", "")}</div></div>', unsafe_allow_html=True)
        st.write("")
        # 加入身體數值顯示
        mc = st.columns(2)
        for i, (l, k, u) in enumerate([("身高", "身高(cm)", "cm"), ("體重", "體重(kg)", "kg"), ("攻擊", "攻擊高度(cm)", "cm"), ("攔網", "攔網高度(cm)", "cm")]):
            if pd.notna(player.get(k)): mc[i%2].metric(l, f"{int(player[k])} {u}")

    with c2:
        st.subheader("🎯 技術雷達圖 (對比基準線)")
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
            # 個人數據 (增加透明填充)
            fig.add_trace(go.Scatterpolar(r=vals+[vals[0]], theta=lbls+[lbls[0]], fill="toself", name=f"{player['姓名']}", line=dict(color=t_color, width=5), fillcolor=_hex_to_rgba(t_color, 0.3)))
            # 位置平均 (橘色)
            fig.add_trace(go.Scatterpolar(r=p_avg+[p_avg[0]], theta=lbls+[lbls[0]], name=f"{player['位置']}平均", line=dict(color=POS_AVG_COLOR, width=3, dash="dot")))
            # 聯盟平均 (深灰色)
            fig.add_trace(go.Scatterpolar(r=l_avg+[l_avg[0]], theta=lbls+[lbls[0]], name="聯盟平均", line=dict(color=LEAGUE_AVG_COLOR, width=2, dash="dash")))
            fig.update_layout(**get_radar_layout())
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("尚無彙總數據")

# ======== 分頁: 戰力對比 ========
def page_compare(data):
    p, s = data["players"], data["summary"]
    if p.empty: return st.warning("資料不足")
    c1, c2 = st.columns(2)
    opts = {f"#{int(r['背號'])} {r['姓名']} ({r.get('球隊','')})": r["player_id"] for _, r in p.iterrows()}
    pa_id = opts[c1.selectbox("🏐 球員 A", list(opts.keys()), index=0)]
    pb_id = opts[c2.selectbox("🏐 球員 B", list(opts.keys()), index=min(1, len(opts)-1))]
    
    sa, sb = s[s["player_id"] == pa_id].iloc[0], s[s["player_id"] == pb_id].iloc[0]
    pa, pb = p[p["player_id"] == pa_id].iloc[0], p[p["player_id"] == pb_id].iloc[0]

    color_a, color_b = TEAM_COLORS.get(pa['球隊'],"#333"), TEAM_COLORS.get(pb['球隊'],"#333")
    if pa['球隊'] == pb['球隊']: color_a, color_b = COMPARE_COLOR_A, COMPARE_COLOR_B

    lbls, v_a, v_b = [], [], []
    for col in STAT_COLUMNS:
        pct = f"{col}%"
        if pd.notna(sa.get(pct)) and pd.notna(sb.get(pct)):
            lbls.append(col); v_a.append(float(sa[pct])); v_b.append(float(sb[pct]))
            
    fig = go.Figure()
    # 增加透明填充，讓重疊部分可見
    fig.add_trace(go.Scatterpolar(r=v_a+[v_a[0]], theta=lbls+[lbls[0]], fill="toself", name=pa['姓名'], line=dict(color=color_a, width=5), fillcolor=_hex_to_rgba(color_a, 0.3)))
    fig.add_trace(go.Scatterpolar(r=v_b+[v_b[0]], theta=lbls+[lbls[0]], fill="toself", name=pb['姓名'], line=dict(color=color_b, width=5), fillcolor=_hex_to_rgba(color_b, 0.3)))
    fig.update_layout(**get_radar_layout())
    st.plotly_chart(fig, use_container_width=True)

    # 對比表格
    st.subheader("📊 數據對比表")
    rows = []
    for col in STAT_COLUMNS:
        va, vb = sa.get(f"{col}%"), sb.get(f"{col}%")
        win_color = color_a if va > vb else (color_b if vb > va else "#666")
        win_text = pa['姓名'] if va > vb else (pb['姓名'] if vb > va else "平手")
        rows.append({"指標": f"{col}%", pa['姓名']: f"{va:.1f}%", pb['姓名']: f"{vb:.1f}%", "優勢": f'<span style="color:{win_color};font-weight:bold;">{win_text}</span>'})
    st.write(pd.DataFrame(rows).to_html(escape=False, index=False), unsafe_allow_html=True)

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