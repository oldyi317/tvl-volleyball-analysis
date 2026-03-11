"""圖表風格設定"""
import matplotlib.pyplot as plt
from config.settings import (
    TEAM_COLOR_PRIMARY, TEAM_COLOR_SECONDARY, TEAM_COLOR_ACCENT,
    DPI, FIGSIZE_DEFAULT,
)

# 預設圖表風格
PALETTE = [TEAM_COLOR_PRIMARY, TEAM_COLOR_SECONDARY, TEAM_COLOR_ACCENT,
           "#E74C3C", "#2ECC71", "#9B59B6", "#F39C12", "#1ABC9C"]


def apply_style():
    """套用專案統一風格"""
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update({
        "font.family": "Microsoft JhengHei",  # 中文字體（必須在 style.use 之後）
        "axes.unicode_minus": False,           # 負號正常顯示
        "figure.figsize": FIGSIZE_DEFAULT,
        "figure.dpi": DPI,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
    })
