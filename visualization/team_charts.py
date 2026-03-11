"""球隊整體統計圖表"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from config.settings import (
    PROCESSED_DIR, FIGURES_DIR, DPI,
    TEAM_COLOR_PRIMARY, TEAM_COLOR_SECONDARY, TEAM_COLOR_ACCENT, PALETTE,
)
from visualization.style import apply_style


def generate_team_charts():
    """產生全部球隊層級圖表"""
    apply_style()
    players = pd.read_csv(PROCESSED_DIR / "players_clean.csv")

    _chart_height_weight(players)
    _chart_position_distribution(players)
    _chart_age_distribution(players)
    _chart_height_by_position(players)

    # 需要比賽彙總的圖表
    summary_path = PROCESSED_DIR / "player_stats_summary.csv"
    if summary_path.exists():
        summary = pd.read_csv(summary_path)
        _chart_scoring_ranking(summary)

    print(f"  ✅ 球隊圖表 → {FIGURES_DIR.name}/")


def _chart_height_weight(players: pd.DataFrame):
    """身高 vs 體重散佈圖"""
    fig, ax = plt.subplots(figsize=(10, 7))
    positions = players["位置"].unique()
    colors = dict(zip(positions, PALETTE[:len(positions)]))

    for pos in positions:
        sub = players[players["位置"] == pos]
        ax.scatter(sub["身高(cm)"], sub["體重(kg)"], s=120, alpha=0.8,
                   color=colors[pos], label=pos, edgecolors="white", linewidth=0.5)
        for _, row in sub.iterrows():
            ax.annotate(row["姓名"], (row["身高(cm)"], row["體重(kg)"]),
                        fontsize=8, ha="left", va="bottom",
                        xytext=(4, 4), textcoords="offset points")

    ax.set_xlabel("身高 (cm)")
    ax.set_ylabel("體重 (kg)")
    ax.set_title("臺北鯨華 — 身高 vs 體重分佈")
    ax.legend(title="位置")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "height_weight_scatter.png", dpi=DPI)
    plt.close(fig)


def _chart_position_distribution(players: pd.DataFrame):
    """位置組成圓餅圖"""
    fig, ax = plt.subplots(figsize=(8, 8))
    counts = players["位置"].value_counts()
    ax.pie(counts.values, labels=counts.index, autopct="%1.0f%%",
           colors=PALETTE[:len(counts)], startangle=90,
           textprops={"fontsize": 12})
    ax.set_title("臺北鯨華 — 陣容位置組成", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "position_pie.png", dpi=DPI)
    plt.close(fig)


def _chart_age_distribution(players: pd.DataFrame):
    """年齡分佈直方圖"""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(players["年齡"].dropna(), bins=range(17, 32), color=TEAM_COLOR_PRIMARY,
            edgecolor="white", alpha=0.85)
    ax.axvline(players["年齡"].mean(), color=TEAM_COLOR_ACCENT, linestyle="--",
               linewidth=2, label=f"平均 {players['年齡'].mean():.1f} 歲")
    ax.set_xlabel("年齡")
    ax.set_ylabel("人數")
    ax.set_title("臺北鯨華 — 球員年齡分佈")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "age_distribution.png", dpi=DPI)
    plt.close(fig)


def _chart_height_by_position(players: pd.DataFrame):
    """各位置身高箱型圖"""
    fig, ax = plt.subplots(figsize=(10, 6))
    order = players.groupby("位置")["身高(cm)"].median().sort_values(ascending=False).index
    sns.boxplot(data=players, x="位置", y="身高(cm)", order=order,
                palette=PALETTE[:len(order)], ax=ax)
    sns.stripplot(data=players, x="位置", y="身高(cm)", order=order,
                  color="black", size=6, alpha=0.5, ax=ax)
    ax.set_title("臺北鯨華 — 各位置身高分佈")
    ax.set_ylabel("身高 (cm)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "height_by_position.png", dpi=DPI)
    plt.close(fig)


def _chart_scoring_ranking(summary: pd.DataFrame):
    """球員得分排行水平條狀圖"""
    if "得分" not in summary.columns:
        return
    ranked = summary[summary["得分"] > 0].nlargest(10, "得分")
    if ranked.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(
        [f"#{int(r['球員背號'])} {r['球員姓名']}" for _, r in ranked.iterrows()],
        ranked["得分"],
        color=TEAM_COLOR_SECONDARY, edgecolor=TEAM_COLOR_PRIMARY
    )
    ax.invert_yaxis()
    ax.set_xlabel("總得分")
    ax.set_title("臺北鯨華 — 球員得分排行")
    for bar, val in zip(bars, ranked["得分"]):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{int(val)}", va="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "scoring_ranking.png", dpi=DPI)
    plt.close(fig)


if __name__ == "__main__":
    generate_team_charts()
