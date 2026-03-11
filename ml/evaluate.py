"""模型評估"""
import numpy as np
from sklearn.metrics import silhouette_score, r2_score, mean_absolute_error


def evaluate_clustering(X, labels) -> float:
    """評估分群品質（Silhouette Score）"""
    if len(set(labels)) < 2:
        return -1.0
    return silhouette_score(X, labels)


def evaluate_regression(model, X, y) -> tuple[float, float]:
    """評估迴歸模型：回傳 (R², MAE)"""
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    return r2, mae
