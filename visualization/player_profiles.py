"""球員個人雷達圖"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from config.settings import (
    PROCESSED_DIR, FIGURES_DIR, STAT_COLUMNS,
    TEAM_COLOR_PRIMARY, TEAM_COLOR_SECONDARY, DPI,
)
from visualization.style import apply_style


def generate_profiles():
    """為每位有數據的球員產生雷達圖，並產生一張全員總覽"""
    apply_style()
    summary = pd.read_csv(PROCESSED_DIR / "player_stats_summary.csv")

    if summary.empty:
        print("  ⚠️  無球員彙總數據，跳過雷達圖")
        return

    # 全員雷達圖總覽
    _generate_overview_radar(summary)

    # 個人雷達圖（只為出賽場次 > 0 的球員）
    active = summary[summary["出賽場次"] > 0]
    for _, row in active.iterrows():
        _generate_single_radar(row, summary)

    print(f"  ✅ 球員雷達圖 → {FIGURES_DIR.name}/ （{len(active)} 張個人 + 1 張總覽）")


def _get_radar_values(row: pd.Series) -> tuple[list[str], list[float]]:
    """從球員彙總中取出雷達圖數值"""
    labels = []
    values = []
    for col in STAT_COLUMNS:
        pct_col = f"{col}%"
        if pct_col in row.index and pd.notna(row[pct_col]):
            labels.append(col)
            values.append(float(row[pct_col]))
    return labels, values


def _generate_single_radar(row: pd.Series, all_summary: pd.DataFrame):
    """產生單一球員雷達圖"""
    labels, values = _get_radar_values(row)
    if len(labels) < 3:
        return

    # 計算全隊平均做對照
    avg_values = []
    for col in labels:
        pct_col = f"{col}%"
        avg_values.append(float(all_summary[pct_col].mean()))

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    values_plot = values + [values[0]]
    avg_plot = avg_values + [avg_values[0]]
    angles += [angles[0]]

    ax.plot(angles, values_plot, "o-", color=TEAM_COLOR_PRIMARY, linewidth=2, label=str(row["球員姓名"]))
    ax.fill(angles, values_plot, alpha=0.25, color=TEAM_COLOR_PRIMARY)
    ax.plot(angles, avg_plot, "o--", color="gray", linewidth=1, alpha=0.6, label="全隊平均")

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_title(f"#{int(row['球員背號'])} {row['球員姓名']}  技術指標雷達圖",
                 fontsize=13, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=9)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"radar_{int(row['球員背號'])}_{row['球員姓名']}.png", dpi=DPI)
    plt.close(fig)


def _generate_overview_radar(summary: pd.DataFrame):
    """全員總覽雷達圖（取出賽場次前 6 名球員）"""
    active = summary[summary["出賽場次"] > 0].nlargest(6, "出賽場次")
    if active.empty:
        return

    labels = [c for c in STAT_COLUMNS if f"{c}%" in summary.columns]
    if len(labels) < 3:
        return

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += [angles[0]]

    colors = [TEAM_COLOR_PRIMARY, TEAM_COLOR_SECONDARY, "#E74C3C",
              "#2ECC71", "#9B59B6", "#F39C12"]

    for i, (_, row) in enumerate(active.iterrows()):
        vals = [float(row.get(f"{c}%", 0)) for c in labels]
        vals += [vals[0]]
        ax.plot(angles, vals, "o-", color=colors[i % len(colors)],
                linewidth=1.5, label=f"#{int(row['球員背號'])} {row['球員姓名']}")

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_title("臺北鯨華 — 主力球員技術指標比較", fontsize=14, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.4, 1.1), fontsize=9)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "radar_overview.png", dpi=DPI)
    plt.close(fig)


if __name__ == "__main__":
    generate_profiles()
