"""爬蟲共用工具"""
import time
import requests
from bs4 import BeautifulSoup
from config.settings import REQUEST_HEADERS, REQUEST_DELAY


def get_soup(url: str, delay: float = REQUEST_DELAY) -> BeautifulSoup:
    """取得網頁並回傳 BeautifulSoup 物件"""
    resp = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
    resp.encoding = "utf-8"
    resp.raise_for_status()
    time.sleep(delay)
    return BeautifulSoup(resp.text, "html.parser")


def parse_stat_pair(text: str) -> tuple[int, int]:
    """
    將 '11 - 25' 格式拆分為 (成功, 總數)
    回傳 (success, total)
    """
    text = text.strip()
    if " - " in text:
        parts = text.split(" - ")
        return int(parts[0]), int(parts[1])
    return 0, 0


def parse_pct(text: str) -> float:
    """將 '44.00%' 或 '0%' 轉為浮點數"""
    text = text.strip().replace("%", "")
    try:
        return float(text)
    except ValueError:
        return 0.0
