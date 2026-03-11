"""特徵工程：從原始數據建構 ML 特徵"""
import pandas as pd
import numpy as np
from config.settings import PROCESSED_DIR, STAT_COLUMNS


def build_player_features() -> pd.DataFrame:
    """
    建構球員層級特徵矩陣
    結合身體素質 + 賽季累計技術指標
    """
    players = pd.read_csv(PROCESSED_DIR / "players_clean.csv")
    summary = pd.read_csv(PROCESSED_DIR / "player_stats_summary.csv")

    # 合併
    df = summary.merge(
        players[["player_id", "位置", "身高(cm)", "體重(kg)", "年齡", "BMI"]],
        on="player_id", how="left"
    )

    # 位置 One-Hot 編碼
    if "位置" in df.columns:
        dummies = pd.get_dummies(df["位置"], prefix="位置")
        df = pd.concat([df, dummies], axis=1)

    return df


def build_match_features() -> pd.DataFrame:
    """
    建構逐場層級特徵（用於預測單場表現）
    加入滾動平均、對手特徵等
    """
    matches = pd.read_csv(PROCESSED_DIR / "matches_clean.csv", parse_dates=["比賽日期"])
    matches.sort_values(["player_id", "比賽日期"], inplace=True)

    # 對手 One-Hot
    if "對手" in matches.columns:
        dummies = pd.get_dummies(matches["對手"], prefix="對手")
        matches = pd.concat([matches, dummies], axis=1)

    # 滾動平均（過去 3 場）
    for col in STAT_COLUMNS:
        pct_col = f"{col}%"
        if pct_col in matches.columns:
            matches[f"{col}_rolling3"] = (
                matches.groupby("player_id")[pct_col]
                .transform(lambda x: x.shift(1).rolling(3, min_periods=1).mean())
            )

    # 場序（該球員的第幾場比賽）
    matches["場序"] = matches.groupby("player_id").cumcount() + 1

    return matches


def get_clustering_features() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    取得用於球員分群的特徵
    回傳 (features_df, meta_df)
    """
    df = build_player_features()

    feature_cols = []
    for col in STAT_COLUMNS:
        pct_col = f"{col}%"
        if pct_col in df.columns:
            feature_cols.append(pct_col)

    body_cols = ["身高(cm)", "體重(kg)", "年齡"]
    feature_cols.extend([c for c in body_cols if c in df.columns])

    features = df[feature_cols].fillna(0)
    meta = df[["player_id", "球員背號", "球員姓名"]].copy()

    return features, meta
