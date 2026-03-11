"""比賽趨勢折線圖"""
import pandas as pd
import matplotlib.pyplot as plt
from config.settings import (
    PROCESSED_DIR, FIGURES_DIR, STAT_COLUMNS, OPPONENTS, DPI,
    TEAM_COLOR_PRIMARY, TEAM_COLOR_ACCENT, PALETTE,
)
from visualization.style import apply_style


def generate_match_trends():
    """產生比賽趨勢相關圖表"""
    apply_style()
    matches = pd.read_csv(PROCESSED_DIR / "matches_clean.csv", parse_dates=["比賽日期"])

    if matches.empty:
        print("  ⚠️  無比賽數據，跳過趨勢圖")
        return

    _chart_team_trend(matches)
    _chart_opponent_comparison(matches)
    _chart_top_players_trend(matches)

    print(f"  ✅ 比賽趨勢圖 → {FIGURES_DIR.name}/")


def _chart_team_trend(matches: pd.DataFrame):
    """全隊各項技術指標月度趨勢"""
    matches = matches.copy()
    matches["年月"] = matches["比賽日期"].dt.to_period("M").dt.to_timestamp()

    pct_cols = [f"{c}%" for c in STAT_COLUMNS if f"{c}%" in matches.columns]
    monthly = matches.groupby("年月")[pct_cols].mean()

    if monthly.empty:
        return

    fig, ax = plt.subplots(figsize=(14, 7))
    for i, col in enumerate(pct_cols):
        ax.plot(monthly.index, monthly[col], "o-", color=PALETTE[i % len(PALETTE)],
                linewidth=2, markersize=6, label=col.replace("%", ""))

    ax.set_xlabel("月份")
    ax.set_ylabel("平均效率 (%)")
    ax.set_title("臺北鯨華 — 全隊技術指標月度趨勢")
    ax.legend(title="指標")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "team_monthly_trend.png", dpi=DPI)
    plt.close(fig)


def _chart_opponent_comparison(matches: pd.DataFrame):
    """對不同對手的表現比較（分組長條圖）"""
    pct_cols = [f"{c}%" for c in ["攻擊", "防守", "接發球"] if f"{c}%" in matches.columns]
    if not pct_cols:
        return

    opp_stats = matches.groupby("對手")[pct_cols].mean()
    opp_stats = opp_stats.reindex([o for o in OPPONENTS if o in opp_stats.index])

    if opp_stats.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    opp_stats.plot(kind="bar", ax=ax, color=PALETTE[:len(pct_cols)], edgecolor="white")
    ax.set_ylabel("平均效率 (%)")
    ax.set_title("臺北鯨華 — 對不同對手的表現")
    ax.set_xticklabels(opp_stats.index, rotation=0)
    ax.legend([c.replace("%", "") for c in pct_cols], title="指標")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "opponent_comparison.png", dpi=DPI)
    plt.close(fig)


def _chart_top_players_trend(matches: pd.DataFrame):
    """主力球員防守效率逐場趨勢（以防守為例）"""
    if "防守%" not in matches.columns:
        return

    # 取出賽紀錄最多的前 5 人
    top_ids = matches.groupby("球員背號").size().nlargest(5).index
    top_matches = matches[matches["球員背號"].isin(top_ids)].copy()

    fig, ax = plt.subplots(figsize=(14, 7))
    for i, (num, grp) in enumerate(top_matches.groupby("球員背號")):
        grp_sorted = grp.sort_values("比賽日期")
        name = grp_sorted["球員姓名"].iloc[0]
        ax.plot(grp_sorted["比賽日期"], grp_sorted["防守%"],
                "o-", color=PALETTE[i % len(PALETTE)], linewidth=1.5,
                markersize=5, alpha=0.8, label=f"#{int(num)} {name}")

    ax.set_xlabel("比賽日期")
    ax.set_ylabel("防守效率 (%)")
    ax.set_title("臺北鯨華 — 主力球員防守效率趨勢")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "defense_trend_top_players.png", dpi=DPI)
    plt.close(fig)


if __name__ == "__main__":
    generate_match_trends()
