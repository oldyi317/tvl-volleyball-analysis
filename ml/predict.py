"""預測推論：載入已訓練模型進行預測"""
import joblib
import pandas as pd
from config.settings import MODELS_DIR


def predict_defense(match_features: pd.DataFrame) -> pd.Series:
    """
    預測防守效率
    match_features: 需含訓練時使用的特徵欄位
    回傳預測的防守效率 (%)
    """
    bundle = joblib.load(MODELS_DIR / "defense_predictor.joblib")
    model = bundle["model"]
    feature_cols = bundle["feature_cols"]

    X = match_features[feature_cols].fillna(0)
    return pd.Series(model.predict(X), index=match_features.index, name="predicted_defense%")


def get_player_cluster(player_features: pd.DataFrame) -> pd.Series:
    """
    預測球員所屬分群
    player_features: 需含分群時使用的特徵欄位
    """
    bundle = joblib.load(MODELS_DIR / "clustering.joblib")
    model = bundle["model"]
    scaler = bundle["scaler"]
    feature_cols = bundle["feature_cols"]

    X = scaler.transform(player_features[feature_cols].fillna(0))
    return pd.Series(model.predict(X), name="cluster")
