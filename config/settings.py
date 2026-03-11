"""全域設定"""
from pathlib import Path

# === 路徑 ===
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = DATA_DIR / "models"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
REPORTS_DIR = OUTPUT_DIR / "reports"
EXCEL_DIR = OUTPUT_DIR / "excel"

# 確保目錄存在
for d in [RAW_DIR, PROCESSED_DIR, MODELS_DIR, FIGURES_DIR, REPORTS_DIR, EXCEL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# === 爬蟲 ===
BASE_URL = "https://tvl.ctvba.org.tw"
TEAM_URL = f"{BASE_URL}/wteam/3"
PLAYER_URL_TEMPLATE = f"{BASE_URL}/wplayer/{{player_id}}"

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
REQUEST_DELAY = 1.0  # 每次請求間隔（秒）

# === 球隊（女子組全部） ===
SEASON = "企21"

WOMEN_TEAMS = {
    "臺北鯨華": {"id": 3, "url": f"{BASE_URL}/wteam/3", "color": "#1B3A6B", "accent": "#4A90D9"},
    "高雄台電": {"id": 4, "url": f"{BASE_URL}/wteam/4", "color": "#D4213D", "accent": "#FF6B6B"},
    "新北中纖": {"id": 5, "url": f"{BASE_URL}/wteam/5", "color": "#2E7D32", "accent": "#66BB6A"},
    "義力營造": {"id": 7, "url": f"{BASE_URL}/wteam/7", "color": "#E65100", "accent": "#FF9800"},
}

TEAM_NAME = "臺北鯨華"  # 預設隊伍（向下相容）

# === 球員位置 ===
POSITIONS = ["主攻手", "副攻手", "中間手", "舉球員", "自由球員", "攻擊手"]

# === 技術指標欄位（比賽數據表） ===
STAT_COLUMNS = ["攻擊", "攔網", "發球", "接發球", "防守", "舉球"]
PCT_COLUMNS = [f"{c}%" for c in STAT_COLUMNS]

# === Opponent name mapping (historical → current) ===
OPPONENT_NAME_MAP = {
    "中國人纖": "新北中纖",
    "新北中國人纖": "新北中纖",
    "凱薩飯店": "義力營造",
    "凱撒飯店": "義力營造",
    "愛山林": "義力營造",
    "高雄台電女排": "高雄台電",
    "臺北鯨華": "臺北鯨華",
}

# Playoff matches: map to actual opponent
PLAYOFF_TAGS = ["挑戰賽", "季後賽", "冠軍賽"]

# === Opponents (current names) ===
OPPONENTS = ["高雄台電", "新北中纖", "義力營造"]

# === 視覺化 ===
TEAM_COLOR_PRIMARY = "#1B3A6B"
TEAM_COLOR_SECONDARY = "#4A90D9"
TEAM_COLOR_ACCENT = "#F5A623"
PALETTE = [TEAM_COLOR_PRIMARY, TEAM_COLOR_SECONDARY, TEAM_COLOR_ACCENT,
           "#E74C3C", "#2ECC71", "#9B59B6", "#F39C12", "#1ABC9C"]
FIGSIZE_DEFAULT = (12, 8)
FIGSIZE_WIDE = (16, 8)
FIGSIZE_SMALL = (8, 6)
DPI = 150
