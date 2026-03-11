"""
Model Training - four ML tasks:
1. Score Prediction (Ridge, RandomForest, GradientBoosting)
2. Performance Prediction (attack/defense efficiency)
3. MVP Composite Ranking (weighted z-score)
4. Anomaly Detection (z-score based)
"""
import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from config.settings import MODELS_DIR, PROCESSED_DIR, STAT_COLUMNS
from ml.feature_engineering import (
    build_match_features, compute_mvp_score,
    detect_anomalies, get_prediction_features,
)
from ml.evaluate import evaluate_regression, compare_models


def train_all():
    """Run all ML training tasks."""
    print("  --- Task 1: Score Prediction ---")
    _train_score_prediction()

    print("\n  --- Task 2: Performance Prediction ---")
    _train_performance_prediction()

    print("\n  --- Task 3: MVP Ranking ---")
    _train_mvp_ranking()

    print("\n  --- Task 4: Anomaly Detection ---")
    _train_anomaly_detection()


# ============================================================
# Task 1: Predict single-game score
# ============================================================
def _train_score_prediction():
    """
    Train 3 models to predict a player's single-game score.
    Compare Ridge vs RandomForest vs GradientBoosting.
    """
    matches = build_match_features()
    if matches.empty or "得分" not in matches.columns:
        print("  ⚠️  No match data, skipping score prediction")
        return

    target = "得分"
    base_features = get_prediction_features()

    # Add opponent & position dummies
    extra = [c for c in matches.columns if c.startswith("vs_") or c.startswith("pos_")]
    feature_cols = [c for c in base_features + extra if c in matches.columns]

    # Filter valid rows (need rolling stats, so skip first few games)
    valid = matches.dropna(subset=[c for c in feature_cols if "rolling" in c]).copy()
    valid = valid[valid["場序"] >= 3]  # at least 3 games of history

    if len(valid) < 15:
        print(f"  ⚠️  Only {len(valid)} valid samples, skipping")
        return

    X = valid[feature_cols].fillna(0)
    y = valid[target]

    # Standardize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Three candidate models
    models = {
        "Ridge": Ridge(alpha=1.0),
        "RandomForest": RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42),
        "GradientBoosting": GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42),
    }

    results = compare_models(models, X_scaled, y, cv=min(5, len(X)))
    best_name = max(results, key=lambda k: results[k]["r2_cv_mean"])
    best_model = models[best_name]
    best_model.fit(X_scaled, y)

    # Save
    joblib.dump({
        "model": best_model,
        "scaler": scaler,
        "feature_cols": feature_cols,
        "model_name": best_name,
    }, MODELS_DIR / "score_predictor.joblib")

    print(f"  ✅ Score Prediction - Best: {best_name}")
    for name, res in results.items():
        marker = " ★" if name == best_name else ""
        print(f"     {name}: R²={res['r2_cv_mean']:.3f}±{res['r2_cv_std']:.3f}, "
              f"MAE={res['mae']:.2f}{marker}")

    # Feature importance (for tree models)
    if hasattr(best_model, "feature_importances_"):
        imp = pd.Series(best_model.feature_importances_, index=feature_cols)
        top5 = imp.nlargest(5)
        print(f"     Top features: {', '.join(f'{k}({v:.3f})' for k, v in top5.items())}")


# ============================================================
# Task 2: Predict attack/defense efficiency
# ============================================================
def _train_performance_prediction():
    """
    Train models to predict attack% and defense%.
    Uses GradientBoosting (best balance of speed and accuracy).
    """
    matches = build_match_features()
    if matches.empty:
        print("  ⚠️  No match data, skipping")
        return

    base_features = get_prediction_features()
    extra = [c for c in matches.columns if c.startswith("vs_") or c.startswith("pos_")]
    feature_cols = [c for c in base_features + extra if c in matches.columns]

    targets = {"攻擊%": "attack_predictor", "防守%": "defense_predictor"}

    for target, filename in targets.items():
        if target not in matches.columns:
            continue

        # Filter: need rolling stats + target > 0
        total_col = target.replace("%", "_總數")
        valid = matches.dropna(subset=[c for c in feature_cols if "rolling" in c]).copy()
        valid = valid[valid["場序"] >= 3]
        if total_col in valid.columns:
            valid = valid[valid[total_col] > 0]

        if len(valid) < 15:
            print(f"  ⚠️  {target}: only {len(valid)} samples, skipping")
            continue

        X = valid[feature_cols].fillna(0)
        y = valid[target]

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
        scores = cross_val_score(model, X_scaled, y, cv=min(5, len(X)), scoring="r2")
        model.fit(X_scaled, y)

        r2, mae = evaluate_regression(model, X_scaled, y)

        joblib.dump({
            "model": model, "scaler": scaler,
            "feature_cols": feature_cols, "target": target,
        }, MODELS_DIR / f"{filename}.joblib")

        print(f"  ✅ {target}: R²={r2:.3f}, MAE={mae:.1f}%, CV={scores.mean():.3f}±{scores.std():.3f}")


# ============================================================
# Task 3: MVP Composite Ranking
# ============================================================
def _train_mvp_ranking():
    """
    Compute MVP scores and save rankings.
    Not a trained model, but a weighted composite scoring system.
    """
    summary = pd.read_csv(PROCESSED_DIR / "player_stats_summary.csv")
    if summary.empty:
        print("  ⚠️  No summary data, skipping")
        return

    mvp = compute_mvp_score(summary)

    # Save
    out_path = PROCESSED_DIR / "mvp_rankings.csv"
    name_col = "球員姓名" if "球員姓名" in mvp.columns else "姓名"
    display_cols = ["MVP_rank", name_col, "球員背號", "MVP_score", "出賽場次"]
    if "球隊" in mvp.columns:
        display_cols.insert(2, "球隊")
    display_cols = [c for c in display_cols if c in mvp.columns]

    mvp.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"  ✅ MVP Rankings saved")

    top5 = mvp.head(5)
    for _, row in top5.iterrows():
        print(f"     #{int(row.get('MVP_rank', 0))} "
              f"{row.get(name_col, '?')} "
              f"({row.get('球隊', '')}) "
              f"Score: {row.get('MVP_score', 0):.1f}")


# ============================================================
# Task 4: Anomaly Detection
# ============================================================
def _train_anomaly_detection():
    """
    Detect exceptional and underperforming games.
    Uses per-player z-score (|z| > 2.0 = anomaly).
    """
    matches = pd.read_csv(PROCESSED_DIR / "matches_clean.csv", parse_dates=["比賽日期"])
    if matches.empty:
        print("  ⚠️  No match data, skipping")
        return

    anomalies = detect_anomalies(matches, threshold=2.0)

    if "is_anomaly" not in anomalies.columns:
        print("  ⚠️  Could not compute anomalies")
        return

    flagged = anomalies[anomalies["is_anomaly"]].copy()

    out_path = PROCESSED_DIR / "anomalies.csv"
    flagged.to_csv(out_path, index=False, encoding="utf-8-sig")

    n_exceptional = len(flagged[flagged["anomaly_type"] == "exceptional"])
    n_under = len(flagged[flagged["anomaly_type"] == "underperform"])

    print(f"  ✅ Anomaly Detection: {len(flagged)} anomalous games found")
    print(f"     Exceptional: {n_exceptional}, Underperform: {n_under}")

    # Show top 3 most extreme
    if not flagged.empty:
        name_col = "球員姓名" if "球員姓名" in flagged.columns else "姓名"
        top3 = flagged.nlargest(3, "max_z")
        for _, row in top3.iterrows():
            print(f"     {row.get(name_col, '?')} "
                  f"vs {row.get('對手', '?')} "
                  f"({row.get('比賽日期', '?'):%Y-%m-%d}): "
                  f"z={row['max_z']:.2f} [{row['anomaly_type']}]")


if __name__ == "__main__":
    train_all()
