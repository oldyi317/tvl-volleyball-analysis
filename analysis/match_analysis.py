"""比賽數據分析"""
import pandas as pd
from config.settings import PROCESSED_DIR, REPORTS_DIR, STAT_COLUMNS, OPPONENTS


def run_match_analysis():
    """產生比賽數據分析報告"""
    matches = pd.read_csv(PROCESSED_DIR / "matches_clean.csv", parse_dates=["比賽日期"])
    summary = pd.read_csv(PROCESSED_DIR / "player_stats_summary.csv")

    lines = []
    lines.append("# 臺北鯨華女子排球隊 — 比賽數據分析\n")

    # --- 各項技術指標排行 ---
    lines.append("## 球員技術指標排行\n")
    for col in STAT_COLUMNS:
        pct_col = f"{col}%"
        total_col = f"{col}_總數"
        if pct_col not in summary.columns or total_col not in summary.columns:
            continue
        # 過濾至少有一定出手次數的球員
        qualified = summary[summary[total_col] >= 5].copy()
        if qualified.empty:
            continue
        top = qualified.nlargest(3, pct_col)
        lines.append(f"### {col}效率 Top 3（至少 5 次）")
        for _, row in top.iterrows():
            lines.append(f"- {row['球員姓名']}：{row[pct_col]:.1f}%"
                          f"（{int(row[f'{col}_成功'])}/{int(row[total_col])}）")
        lines.append("")

    # --- 對手分析 ---
    lines.append("## 對手分析\n")
    if "對手" in matches.columns:
        for opp in OPPONENTS:
            opp_df = matches[matches["對手"] == opp]
            if opp_df.empty:
                continue
            lines.append(f"### vs {opp}（{len(opp_df)} 人次出賽紀錄）")
            for col in STAT_COLUMNS:
                pct_col = f"{col}%"
                if pct_col in opp_df.columns:
                    avg = opp_df[pct_col].mean()
                    lines.append(f"- {col} 平均效率：{avg:.1f}%")
            lines.append("")

    # --- 月份趨勢 ---
    lines.append("## 月份表現趨勢\n")
    if "比賽日期" in matches.columns:
        matches["年月"] = matches["比賽日期"].dt.to_period("M")
        for col in ["防守", "接發球"]:
            pct_col = f"{col}%"
            if pct_col in matches.columns:
                monthly = matches.groupby("年月")[pct_col].mean()
                lines.append(f"### {col}效率月均")
                for period, val in monthly.items():
                    lines.append(f"- {period}：{val:.1f}%")
                lines.append("")

    report_text = "\n".join(lines)
    out_path = REPORTS_DIR / "match_analysis.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"  ✅ 比賽分析報告 → {out_path.name}")

    return report_text


if __name__ == "__main__":
    print(run_match_analysis())
