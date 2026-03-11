"""Prediction utilities - load trained models and predict."""
import joblib
import pandas as pd
from config.settings import MODELS_DIR


def predict_score(match_features: pd.DataFrame) -> pd.Series:
    """Predict single-game score."""
    return _predict_with_model("score_predictor.joblib", match_features, "predicted_score")


def predict_attack(match_features: pd.DataFrame) -> pd.Series:
    """Predict attack efficiency %."""
    return _predict_with_model("attack_predictor.joblib", match_features, "predicted_attack%")


def predict_defense(match_features: pd.DataFrame) -> pd.Series:
    """Predict defense efficiency %."""
    return _predict_with_model("defense_predictor.joblib", match_features, "predicted_defense%")


def _predict_with_model(model_file: str, features: pd.DataFrame, output_name: str) -> pd.Series:
    """Generic prediction using a saved model."""
    path = MODELS_DIR / model_file
    if not path.exists():
        raise FileNotFoundError(f"Model not found: {path}. Run training first.")

    bundle = joblib.load(path)
    model = bundle["model"]
    scaler = bundle["scaler"]
    feature_cols = bundle["feature_cols"]

    X = features[feature_cols].fillna(0)
    X_scaled = scaler.transform(X)
    return pd.Series(model.predict(X_scaled), index=features.index, name=output_name)
