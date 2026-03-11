"""描述性統計分析"""
import pandas as pd
from config.settings import PROCESSED_DIR, REPORTS_DIR


def run_stats():
    players = pd.read_csv(PROCESSED_DIR / "players_clean.csv")
    summary_path = PROCESSED_DIR / "player_stats_summary.csv"
    summary = pd.read_csv(summary_path) if summary_path.exists() else pd.DataFrame()

    lines = []
    lines.append("# 臺北鯨華女子排球隊 — 描述性統計報告\n")

    # 陣容組成
    if "位置" in players.columns:
        lines.append("## 陣容組成\n")
        for pos, cnt in players["位置"].value_counts().items():
            lines.append(f"- {pos}：{cnt} 人")
        lines.append("")

    # 身體素質
    lines.append("## 身體素質統計\n")
    body_cols = ["身高(cm)", "體重(kg)", "BMI", "年齡"]
    for col in body_cols:
        if col not in players.columns:
            continue
        s = players[col].dropna()
        if s.empty:
            continue
        lines.append(f"### {col}")
        lines.append(f"- 平均：{s.mean():.1f}")
        lines.append(f"- 中位數：{s.median():.1f}")
        name_col = "姓名" if "姓名" in players.columns else None
        if name_col:
            lines.append(f"- 最小：{s.min():.0f}（{players.loc[s.idxmin(), name_col]}）")
            lines.append(f"- 最大：{s.max():.0f}（{players.loc[s.idxmax(), name_col]}）")
        lines.append(f"- 標準差：{s.std():.1f}")
        lines.append("")

    # 各位置平均
    if "位置" in players.columns:
        available = [c for c in ["身高(cm)", "體重(kg)", "年齡"] if c in players.columns]
        if available:
            lines.append("## 各位置平均身體素質\n")
            pos_stats = players.groupby("位置")[available].mean().round(1)
            lines.append(pos_stats.to_markdown())
            lines.append("")

    # 賽季出賽
    if not summary.empty and "出賽場次" in summary.columns:
        lines.append("## 賽季出賽統計\n")
        lines.append(f"- 全隊總出賽人次：{summary['出賽場次'].sum()}")
        lines.append(f"- 平均每人出賽：{summary['出賽場次'].mean():.1f} 場")
        name_col = "球員姓名" if "球員姓名" in summary.columns else None
        if name_col:
            top_idx = summary["出賽場次"].idxmax()
            lines.append(f"- 最多出賽：{summary.loc[top_idx, name_col]}"
                          f"（{summary['出賽場次'].max()} 場）")
        if "得分" in summary.columns and name_col:
            top_scorer_idx = summary["得分"].idxmax()
            lines.append(f"- 得分王：{summary.loc[top_scorer_idx, name_col]}"
                          f"（{int(summary.loc[top_scorer_idx, '得分'])} 分）")
        lines.append("")

    report_text = "\n".join(lines)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / "descriptive_stats.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"  ✅ 描述性統計報告 → {out_path.name}")


if __name__ == "__main__":
    run_stats()
