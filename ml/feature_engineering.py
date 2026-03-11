"""
Feature Engineering - build features for all ML tasks

Features:
- Rolling averages (past 3/5 games)
- Opponent one-hot encoding
- Position one-hot encoding
- Physical attributes (height, weight, age)
- Game sequence number
- MVP composite score
"""
import pandas as pd
import numpy as np
from config.settings import PROCESSED_DIR, STAT_COLUMNS


def build_match_features() -> pd.DataFrame:
    """
    Build per-match features for prediction models.
    Each row = one player in one game, with rolling stats as features.
    """
    matches = pd.read_csv(PROCESSED_DIR / "matches_clean.csv", parse_dates=["比賽日期"])
    players = pd.read_csv(PROCESSED_DIR / "players_clean.csv")

    if matches.empty:
        return pd.DataFrame()

    matches.sort_values(["player_id", "比賽日期"], inplace=True)

    # Merge physical attributes
    phys_cols = [c for c in ["player_id", "位置", "身高(cm)", "體重(kg)", "年齡", "BMI"] if c in players.columns]
    if phys_cols and "player_id" in players.columns:
        matches = matches.merge(players[phys_cols], on="player_id", how="left", suffixes=("", "_dup"))
        # Remove duplicate columns
        matches = matches[[c for c in matches.columns if not c.endswith("_dup")]]

    # Rolling averages (past 3 and 5 games) for each stat
    for col in STAT_COLUMNS:
        pct_col = f"{col}%"
        if pct_col not in matches.columns:
            continue
        for window in [3, 5]:
            matches[f"{col}_rolling{window}"] = (
                matches.groupby("player_id")[pct_col]
                .transform(lambda x: x.shift(1).rolling(window, min_periods=1).mean())
            )
        # Rolling std (variability indicator)
        matches[f"{col}_std3"] = (
            matches.groupby("player_id")[pct_col]
            .transform(lambda x: x.shift(1).rolling(3, min_periods=2).std())
        )

    # Score rolling
    if "得分" in matches.columns:
        for window in [3, 5]:
            matches[f"得分_rolling{window}"] = (
                matches.groupby("player_id")["得分"]
                .transform(lambda x: x.shift(1).rolling(window, min_periods=1).mean())
            )

    # Game sequence number
    matches["場序"] = matches.groupby("player_id").cumcount() + 1

    # Opponent one-hot
    if "對手" in matches.columns:
        dummies = pd.get_dummies(matches["對手"], prefix="vs")
        matches = pd.concat([matches, dummies], axis=1)

    # Position one-hot
    if "位置" in matches.columns:
        dummies = pd.get_dummies(matches["位置"], prefix="pos")
        matches = pd.concat([matches, dummies], axis=1)

    return matches


def compute_mvp_score(summary: pd.DataFrame = None) -> pd.DataFrame:
    """
    Compute MVP composite score using weighted z-scores.

    Weights reflect volleyball importance:
    - Attack efficiency: 0.25
    - Block efficiency: 0.15
    - Serve efficiency: 0.15
    - Receive efficiency: 0.15
    - Defense efficiency: 0.15
    - Setting efficiency: 0.05
    - Total points: 0.10
    """
    if summary is None:
        summary = pd.read_csv(PROCESSED_DIR / "player_stats_summary.csv")

    if summary.empty:
        return summary

    weights = {
        "攻擊%": 0.25, "攔網%": 0.15, "發球%": 0.15,
        "接發球%": 0.15, "防守%": 0.15, "舉球%": 0.05,
    }

    df = summary.copy()

    # Z-score normalization for each stat
    z_cols = []
    for col, w in weights.items():
        if col not in df.columns:
            continue
        z_col = f"{col}_z"
        mean = df[col].mean()
        std = df[col].std()
        if std > 0:
            df[z_col] = (df[col] - mean) / std
        else:
            df[z_col] = 0
        z_cols.append((z_col, w))

    # Add points z-score
    if "得分" in df.columns:
        mean = df["得分"].mean()
        std = df["得分"].std()
        if std > 0:
            df["得分_z"] = (df["得分"] - mean) / std
            z_cols.append(("得分_z", 0.10))

    # Weighted sum
    df["MVP_score"] = sum(df[col] * w for col, w in z_cols)

    # Normalize to 0-100 scale
    min_s, max_s = df["MVP_score"].min(), df["MVP_score"].max()
    if max_s > min_s:
        df["MVP_score"] = ((df["MVP_score"] - min_s) / (max_s - min_s) * 100).round(1)
    else:
        df["MVP_score"] = 50.0

    # Rank
    df["MVP_rank"] = df["MVP_score"].rank(ascending=False).astype(int)
    df.sort_values("MVP_rank", inplace=True)

    return df


def detect_anomalies(matches: pd.DataFrame = None, threshold: float = 2.0) -> pd.DataFrame:
    """
    Detect anomalous performances using z-score per player.
    threshold: number of std deviations to flag as anomaly.

    Returns DataFrame with anomaly flags and z-scores.
    """
    if matches is None:
        matches = pd.read_csv(PROCESSED_DIR / "matches_clean.csv", parse_dates=["比賽日期"])

    if matches.empty:
        return pd.DataFrame()

    df = matches.copy()
    anomaly_cols = []

    for col in STAT_COLUMNS:
        pct_col = f"{col}%"
        if pct_col not in df.columns:
            continue

        z_col = f"{col}_z"
        # Z-score within each player
        df[z_col] = df.groupby("player_id")[pct_col].transform(
            lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0
        )
        anomaly_cols.append(z_col)

    if "得分" in df.columns:
        df["得分_z"] = df.groupby("player_id")["得分"].transform(
            lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0
        )
        anomaly_cols.append("得分_z")

    # Flag anomalies: any stat with |z| > threshold
    if anomaly_cols:
        df["max_z"] = df[anomaly_cols].abs().max(axis=1)
        df["is_anomaly"] = df["max_z"] >= threshold
        df["anomaly_type"] = "normal"
        df.loc[df["is_anomaly"] & (df[anomaly_cols].max(axis=1) >= threshold), "anomaly_type"] = "exceptional"
        df.loc[df["is_anomaly"] & (df[anomaly_cols].min(axis=1) <= -threshold), "anomaly_type"] = "underperform"

    return df


def get_prediction_features() -> list[str]:
    """Return list of feature column names used for prediction models."""
    features = []
    for col in STAT_COLUMNS:
        features.extend([f"{col}_rolling3", f"{col}_rolling5", f"{col}_std3"])
    features.extend(["得分_rolling3", "得分_rolling5", "場序"])
    # Physical
    features.extend(["身高(cm)", "體重(kg)", "年齡"])
    return features
