"""Model evaluation utilities."""
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import cross_val_score


def evaluate_regression(model, X, y) -> tuple[float, float]:
    """Evaluate regression: returns (R2, MAE)."""
    y_pred = model.predict(X)
    return r2_score(y, y_pred), mean_absolute_error(y, y_pred)


def compare_models(models: dict, X, y, cv: int = 5) -> dict:
    """
    Compare multiple models using cross-validation.
    Returns dict of {name: {r2_cv_mean, r2_cv_std, mae}}.
    """
    results = {}
    for name, model in models.items():
        scores = cross_val_score(model, X, y, cv=cv, scoring="r2")
        model.fit(X, y)
        y_pred = model.predict(X)
        mae = mean_absolute_error(y, y_pred)
        results[name] = {
            "r2_cv_mean": scores.mean(),
            "r2_cv_std": scores.std(),
            "mae": mae,
        }
    return results
