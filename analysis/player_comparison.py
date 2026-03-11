"""球員間比較分析"""
import pandas as pd
from config.settings import PROCESSED_DIR, STAT_COLUMNS


def compare_players(player_ids: list[int] = None) -> pd.DataFrame:
    """
    比較指定球員的賽季統計
    若未指定 player_ids，則比較全部球員
    """
    summary = pd.read_csv(PROCESSED_DIR / "player_stats_summary.csv")
    if player_ids:
        summary = summary[summary["player_id"].isin(player_ids)]

    display_cols = ["球員背號", "球員姓名", "出賽場次"]
    for col in STAT_COLUMNS:
        pct_col = f"{col}%"
        if pct_col in summary.columns:
            display_cols.append(pct_col)
    if "得分" in summary.columns:
        display_cols.append("得分")

    return summary[[c for c in display_cols if c in summary.columns]]


def rank_players_by(stat: str = "得分") -> pd.DataFrame:
    """依指定統計指標排行"""
    summary = pd.read_csv(PROCESSED_DIR / "player_stats_summary.csv")
    if stat not in summary.columns:
        raise ValueError(f"欄位 '{stat}' 不存在，可用：{list(summary.columns)}")
    return summary.nlargest(len(summary), stat)[["球員背號", "球員姓名", stat]]


def position_comparison() -> pd.DataFrame:
    """各位置平均表現比較"""
    players = pd.read_csv(PROCESSED_DIR / "players_clean.csv")
    summary = pd.read_csv(PROCESSED_DIR / "player_stats_summary.csv")
    merged = summary.merge(players[["player_id", "位置"]], on="player_id", how="left")

    pct_cols = [f"{c}%" for c in STAT_COLUMNS if f"{c}%" in merged.columns]
    result = merged.groupby("位置")[pct_cols + ["得分", "出賽場次"]].mean().round(2)
    return result
