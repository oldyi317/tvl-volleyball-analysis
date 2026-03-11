"""模型訓練：球員分群 + 表現預測"""
import joblib
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score
from config.settings import MODELS_DIR, PROCESSED_DIR, STAT_COLUMNS
from ml.feature_engineering import get_clustering_features, build_match_features
from ml.evaluate import evaluate_clustering, evaluate_regression


def train_model():
    """執行所有模型訓練"""
    _train_clustering()
    _train_performance_predictor()


def _train_clustering():
    """
    球員分群（K-Means）
    依技術指標 + 身體素質將球員分成不同類型
    """
    features, meta = get_clustering_features()

    if len(features) < 3:
        print("  ⚠️  球員數不足，跳過分群")
        return

    scaler = StandardScaler()
    X = scaler.fit_transform(features)

    # 自動選擇 k（2~5，取最佳 silhouette）
    best_k, best_score = 2, -1
    for k in range(2, min(6, len(features))):
        km = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = km.fit_predict(X)
        score = evaluate_clustering(X, labels)
        if score > best_score:
            best_k, best_score = k, score

    # 用最佳 k 訓練
    km = KMeans(n_clusters=best_k, n_init=10, random_state=42)
    labels = km.fit_predict(X)

    # 儲存
    joblib.dump({"model": km, "scaler": scaler, "feature_cols": list(features.columns)},
                MODELS_DIR / "clustering.joblib")

    # 輸出結果
    meta["cluster"] = labels
    meta.to_csv(PROCESSED_DIR / "player_clusters.csv", index=False, encoding="utf-8-sig")

    print(f"  ✅ 球員分群完成：{best_k} 群（silhouette = {best_score:.3f}）")
    for c in range(best_k):
        members = meta[meta["cluster"] == c]["球員姓名"].tolist()
        print(f"     群 {c}: {', '.join(members)}")


def _train_performance_predictor():
    """
    表現預測模型（Ridge Regression）
    用滾動平均 + 對手 + 身體素質預測防守效率
    """
    matches = build_match_features()
    target = "防守%"

    if target not in matches.columns:
        print("  ⚠️  無防守數據，跳過預測模型")
        return

    # 選擇特徵
    feature_cols = [c for c in matches.columns if c.endswith("_rolling3")]
    feature_cols += [c for c in matches.columns if c.startswith("對手_")]
    feature_cols += ["場序"]
    feature_cols = [c for c in feature_cols if c in matches.columns]

    # 排除前幾場（沒有滾動平均）和目標為 0 的場次
    valid = matches.dropna(subset=feature_cols + [target])
    valid = valid[valid["防守_總數"] > 0]  # 至少有防守次數

    if len(valid) < 10:
        print(f"  ⚠️  有效樣本僅 {len(valid)} 筆，跳過預測模型")
        return

    X = valid[feature_cols].fillna(0)
    y = valid[target]

    # 訓練
    model = Ridge(alpha=1.0)
    scores = cross_val_score(model, X, y, cv=min(5, len(X)), scoring="r2")
    model.fit(X, y)

    # 儲存
    joblib.dump({"model": model, "feature_cols": feature_cols},
                MODELS_DIR / "defense_predictor.joblib")

    r2, mae = evaluate_regression(model, X, y)
    print(f"  ✅ 防守效率預測模型：R² = {r2:.3f}, MAE = {mae:.1f}%")
    print(f"     交叉驗證 R²：{scores.mean():.3f} ± {scores.std():.3f}")


if __name__ == "__main__":
    train_model()
