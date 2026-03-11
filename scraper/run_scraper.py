"""爬蟲執行入口：支援單隊或全聯盟爬取"""
import json
from tqdm import tqdm
from config.settings import RAW_DIR, WOMEN_TEAMS
from scraper.team_scraper import scrape_team_page
from scraper.player_scraper import scrape_player_page


def run(team_name: str = None):
    """
    執行爬蟲流程
    team_name: 指定隊名（如 "臺北鯨華"），None 則爬全部
    """
    teams_to_scrape = {}
    if team_name:
        if team_name not in WOMEN_TEAMS:
            raise ValueError(f"找不到隊伍 '{team_name}'，可用：{list(WOMEN_TEAMS.keys())}")
        teams_to_scrape[team_name] = WOMEN_TEAMS[team_name]
    else:
        teams_to_scrape = WOMEN_TEAMS

    all_league_players = {}
    all_league_matches = {}

    for tname, tinfo in teams_to_scrape.items():
        print(f"\n  📡 [{tname}] 正在讀取球隊頁面...")
        team_data = scrape_team_page(team_url=tinfo["url"])
        player_stubs = team_data["players"]
        print(f"     找到 {len(player_stubs)} 位球員、"
              f"{len(team_data['coaches'])} 位教練、"
              f"{len(team_data['admin'])} 位行政人員")

        # 儲存教練 & 行政
        _save_json(team_data["coaches"], RAW_DIR / f"{tname}_coaches.json")
        _save_json(team_data["admin"], RAW_DIR / f"{tname}_admin.json")

        # 逐一抓取球員個人頁面
        print(f"  📥 [{tname}] 正在抓取球員個人頁面...")
        team_players = []
        team_matches = []

        for stub in tqdm(player_stubs, desc=f"     {tname}"):
            pid = stub["player_id"]
            try:
                detail = scrape_player_page(pid)
                merged = {**stub, **detail, "球隊": tname}
                team_players.append(merged)

                for m in detail.get("逐場數據", []):
                    m["player_id"] = pid
                    m["球員姓名"] = detail.get("姓名", stub.get("姓名", ""))
                    m["球員背號"] = detail.get("背號", stub.get("背號", ""))
                    m["球隊"] = tname
                    team_matches.append(m)

            except Exception as e:
                print(f"     ⚠️  #{stub.get('背號','?')} {stub.get('姓名','未知')} 失敗：{e}")

        # 儲存單隊資料
        _save_json({"球隊": tname, "球員": team_players}, RAW_DIR / f"{tname}_players.json")
        _save_json(team_matches, RAW_DIR / f"{tname}_match_records.json")

        all_league_players[tname] = team_players
        all_league_matches[tname] = team_matches

        print(f"  ✅ [{tname}] 完成！{len(team_players)} 位球員、{len(team_matches)} 筆比賽紀錄")

    # 合併全聯盟資料
    combined_players = []
    combined_matches = []
    for tname in all_league_players:
        combined_players.extend(all_league_players[tname])
        combined_matches.extend(all_league_matches[tname])

    _save_json({"球隊": "全聯盟", "球員": combined_players}, RAW_DIR / "players.json")
    _save_json(combined_matches, RAW_DIR / "match_records.json")

    total_p = len(combined_players)
    total_m = len(combined_matches)
    print(f"\n  🏆 全部完成！共 {len(teams_to_scrape)} 隊、{total_p} 位球員、{total_m} 筆比賽紀錄")
    print(f"     資料儲存於 {RAW_DIR}")


def _save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    run()
