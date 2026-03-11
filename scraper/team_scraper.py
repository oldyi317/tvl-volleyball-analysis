"""球隊頁面爬蟲：取得球員清單、教練團、行政團隊

實際 HTML 結構（2026-03 確認）：
- 球員卡片在 div.player_list > div.col-md-3 裡
- <a> 只包含 <img>，球員資訊在旁邊的 <div> 兄弟元素中
- 背號在 h3.player_number 裡：<small>#</small>1
- 姓名+位置在另一個 h3.fs16 裡：林良黛 <span>主攻手</span>
- 教練在 div.coach_list > div.col-md-3 裡：<h3>職稱</h3><p>姓名</p>
"""
import re
from config.settings import TEAM_URL, BASE_URL, POSITIONS
from scraper.utils import get_soup


def scrape_team_page(team_url: str = None) -> dict:
    url = team_url or TEAM_URL
    soup = get_soup(url)
    return {
        "players": _parse_players(soup),
        "coaches": _parse_coaches(soup),
        "admin": _parse_admin(soup),
    }


def _normalize_url(url: str) -> str:
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return BASE_URL + url
    return url


def _parse_players(soup) -> list[dict]:
    """解析球員卡片"""
    players = []
    seen = set()

    # 找 div.player_list 容器
    player_list = soup.find("div", class_="player_list")
    if not player_list:
        # fallback: 找所有含 wplayer 連結的容器
        player_list = soup

    # 每位球員是一個 div.col-md-3.col-6.mb-grid-gutter
    cards = player_list.find_all("div", class_=re.compile(r"mb-grid-gutter"))

    for card in cards:
        # 找 <a> 連結取得 player_id 和照片
        link = card.find("a", href=re.compile(r"wplayer"))
        if not link:
            continue

        href = _normalize_url(link.get("href", ""))
        pid_match = re.search(r"/wplayer/(\d+)", href)
        if not pid_match:
            continue
        pid = int(pid_match.group(1))
        if pid in seen:
            continue
        seen.add(pid)

        player = {"player_id": pid, "個人頁面": href}

        # 照片
        img = link.find("img")
        if img and img.get("src"):
            player["照片網址"] = _normalize_url(img["src"])

        # 背號：h3.player_number 裡面是 <small>#</small>數字
        num_h3 = card.find("h3", class_=re.compile(r"player_number"))
        if num_h3:
            num_text = num_h3.get_text(strip=True).replace("#", "")
            if num_text.isdigit():
                player["背號"] = int(num_text)

        # 姓名 + 位置：h3.fs16 裡面是「林良黛 <span>主攻手</span>」
        name_h3 = card.find("h3", class_=re.compile(r"fs16"))
        if name_h3:
            full_text = name_h3.get_text(strip=True)

            # 位置通常在 <span> 裡
            pos_span = name_h3.find("span")
            pos_text = pos_span.get_text(strip=True) if pos_span else ""

            # 姓名 = 全文去掉位置部分
            name = full_text.replace(pos_text, "").strip()

            # 處理隊長標記
            if "(隊長)" in name:
                name = name.replace("(隊長)", "").strip()
                player["備註"] = "隊長"

            if name:
                player["姓名"] = name

            # 比對標準位置名稱
            for pos in POSITIONS:
                if pos in pos_text or pos in full_text:
                    player["位置"] = pos
                    break
            else:
                # 如果是簡稱如 "主攻" 沒有 "手"
                pos_map = {"主攻": "主攻手", "副攻": "副攻手", "中間": "中間手",
                           "舉球": "舉球員", "自由": "自由球員"}
                for short, full in pos_map.items():
                    if short in pos_text or short in full_text:
                        player["位置"] = full
                        break

        # 如果 h3.fs16 找不到，嘗試從 h3.mb-0 等備用選擇器
        if "姓名" not in player:
            for h3 in card.find_all("h3"):
                text = h3.get_text(strip=True)
                if any(pos in text for pos in POSITIONS) or any(p in text for p in ["主攻", "副攻", "中間", "舉球", "自由"]):
                    for pos in POSITIONS:
                        if pos in text:
                            name = text.replace(pos, "").replace("(隊長)", "").strip()
                            player["姓名"] = name
                            player["位置"] = pos
                            break

        # 生日/身高/體重：可能在 <em> 或 <span> 中
        for em in card.find_all(["em", "span"]):
            t = em.get_text(strip=True)
            if re.match(r"\d{4}\.\d{2}\.\d{2}", t):
                player["生日"] = t.replace(".", "-")
            elif re.match(r"\d{3,4}cm$", t.replace(" ", "")):
                player["身高(cm)"] = int(t.replace("cm", "").strip())
            elif re.match(r"\d{2,3}kg$", t.replace(" ", "")):
                player["體重(kg)"] = int(t.replace("kg", "").strip())

        if player.get("姓名") or player.get("player_id"):
            players.append(player)

    players.sort(key=lambda x: x.get("背號", 999))
    return players


def _parse_coaches(soup) -> list[dict]:
    """解析教練團：div.coach_list > div 裡的 <h3>職稱</h3><p>姓名</p>"""
    coaches = []
    coach_list = soup.find("div", class_="coach_list")
    if not coach_list:
        return coaches

    for card in coach_list.find_all("div", class_=re.compile(r"mb-grid-gutter")):
        h3 = card.find("h3")
        p = card.find("p")
        if h3 and p:
            entry = {"職稱": h3.get_text(strip=True), "姓名": p.get_text(strip=True)}
            img = card.find("img")
            if img and img.get("src") and "no-pic" not in img.get("src", ""):
                entry["照片網址"] = _normalize_url(img["src"])
            coaches.append(entry)

    return coaches


def _parse_admin(soup) -> list[dict]:
    """解析行政團隊（結構同教練）"""
    admin = []
    # 行政團隊可能在 id="supervisor_list" 的 tab 下
    admin_section = soup.find("div", id="supervisor_list")
    if not admin_section:
        # fallback: 找含有 "領隊" 或 "管理" 文字的區塊
        for h3 in soup.find_all("h3"):
            text = h3.get_text(strip=True)
            if text in ["領隊", "管理", "經理", "秘書"]:
                card = h3.parent
                p = card.find("p") if card else None
                if p:
                    entry = {"職稱": text, "姓名": p.get_text(strip=True)}
                    img = card.find("img") if card else None
                    if img and img.get("src") and "no-pic" not in img.get("src", ""):
                        entry["照片網址"] = _normalize_url(img["src"])
                    admin.append(entry)
        return admin

    for card in admin_section.find_all("div", class_=re.compile(r"mb-grid-gutter")):
        h3 = card.find("h3")
        p = card.find("p")
        if h3 and p:
            entry = {"職稱": h3.get_text(strip=True), "姓名": p.get_text(strip=True)}
            img = card.find("img")
            if img and img.get("src") and "no-pic" not in img.get("src", ""):
                entry["照片網址"] = _normalize_url(img["src"])
            admin.append(entry)

    return admin
