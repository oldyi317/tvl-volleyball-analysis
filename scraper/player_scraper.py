"""球員個人頁面爬蟲：詳細資料 + 逐場數據"""
import re
from config.settings import BASE_URL, POSITIONS, PLAYER_URL_TEMPLATE
from scraper.utils import get_soup


def scrape_player_page(player_id: int) -> dict:
    """
    從 /wplayer/{id} 擷取球員完整資料
    回傳 dict 含基本資料、逐場數據、累計數據
    """
    url = PLAYER_URL_TEMPLATE.format(player_id=player_id)
    soup = get_soup(url)
    text_all = soup.get_text()

    info = {"player_id": player_id, "個人頁面": url}

    # --- 姓名（從頁面 title） ---
    title = soup.find("title")
    if title:
        m = re.match(r"(.+?)\s*-\s*", title.get_text(strip=True))
        if m:
            info["姓名"] = m.group(1).strip()

    # --- 背號 ---
    for s in soup.find_all(string=re.compile(r"^#\d+$")):
        m = re.match(r"#(\d+)", s.strip())
        if m:
            info["背號"] = int(m.group(1))
            break

    # --- 位置 ---
    for pos in POSITIONS:
        if pos in text_all:
            info["位置"] = pos
            break

    # --- 身體數值（正規表達式逐一比對） ---
    patterns = {
        "身高(cm)":    r"身高\s*Height\s*(\d+)\s*cm",
        "體重(kg)":    r"體重\s*Weight\s*(\d+)\s*kg",
        "攻擊高度(cm)": r"攻擊高度\s*Attack\s*(\d+)\s*cm",
        "攔網高度(cm)": r"攔網高度\s*Block\s*(\d+)\s*cm",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text_all)
        if m:
            info[key] = int(m.group(1))

    # --- 生日 ---
    m = re.search(r"生日\s*/\s*年齡\s*(\d{4}-\d{2}-\d{2})", text_all)
    if m:
        info["生日"] = m.group(1)

    # --- MBTI ---
    m = re.search(r"MBTI\s*類型\s*([A-Z]{4})", text_all)
    if m:
        info["MBTI"] = m.group(1)

    # --- 照片 ---
    img = soup.find("img", attrs={"alt": "Player"})
    if img and img.get("src"):
        src = img["src"]
        if src.startswith("/"):
            src = BASE_URL + src
        info["照片網址"] = src

    # --- 逐場比賽數據 ---
    info["逐場數據"], info["累計數據"] = _parse_match_table(soup)
    info["出賽場次"] = len(info["逐場數據"])

    return info


def _parse_match_table(soup) -> tuple[list[dict], dict]:
    """解析比賽數據表格，回傳 (逐場列表, 累計字典)"""
    matches = []
    cumulative = {}
    header = None

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            ths = row.find_all("th")
            if ths and any("比賽日期" in th.get_text() for th in ths):
                header = [th.get_text(strip=True) for th in ths]
                continue

            if not header:
                continue

            tds = row.find_all("td")
            if len(tds) < len(header):
                continue

            cells = []
            for i, td in enumerate(tds[:len(header)]):
                link = td.find("a")
                cells.append(link.get_text(strip=True) if link and header[i] == "效力球隊" else td.get_text(strip=True))

            row_dict = dict(zip(header, cells))

            # 判斷是否為累計行
            if "球員累計" in cells:
                skip_keys = {"季", "比賽日期", "效力球隊", "對手"}
                cumulative = {k: v for k, v in row_dict.items() if k not in skip_keys}
            elif row_dict.get("比賽日期"):
                matches.append(row_dict)

    return matches, cumulative
