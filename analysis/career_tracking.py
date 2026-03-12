"""
Player career tracking across seasons.
Builds career history from historical roster data.
"""
import json
from pathlib import Path
from collections import defaultdict
from config.settings import WOMEN_TEAMS

ROSTER_PATH = Path(__file__).parent.parent / "data" / "rosters.json"

# Map old team names to current
TEAM_NORMALIZE = {
    "愛山林": "義力營造",
    "凱撒飯店": "義力營造",
    "中國人纖": "新北中纖",
    "高雄台電女排": "高雄台電",
}


def load_rosters() -> dict:
    """Load historical roster JSON."""
    if not ROSTER_PATH.exists():
        return {}
    with open(ROSTER_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Remove metadata key
    return {k: v for k, v in data.items() if not k.startswith("_")}


def build_career_table() -> list[dict]:
    """
    Build a flat table of player-season records.
    Each row = one player in one season on one team.
    """
    rosters = load_rosters()
    records = []

    for season, teams in rosters.items():
        for team, players in teams.items():
            current_team = TEAM_NORMALIZE.get(team, team)
            for p in players:
                records.append({
                    "season": season,
                    "team_original": team,
                    "team_current": current_team,
                    "num": p.get("num"),
                    "name": p["name"],
                    "pos": p.get("pos", ""),
                    "captain": p.get("captain", False),
                    "foreign": p.get("foreign", False),
                })

    return records


def get_player_career(name: str) -> list[dict]:
    """Get career history for a specific player."""
    records = build_career_table()
    return [r for r in records if r["name"] == name]


def get_player_transfers() -> list[dict]:
    """
    Detect players who changed teams across seasons.
    Returns list of transfer records.
    """
    rosters = load_rosters()
    # player_name -> [(season, team), ...]
    player_teams = defaultdict(list)

    for season, teams in sorted(rosters.items()):
        for team, players in teams.items():
            current_team = TEAM_NORMALIZE.get(team, team)
            for p in players:
                if not p.get("foreign", False):  # skip foreign players
                    player_teams[p["name"]].append((season, current_team))

    transfers = []
    for name, history in player_teams.items():
        # Check if player appeared on different teams
        seen_teams = []
        for season, team in history:
            if seen_teams and seen_teams[-1][1] != team:
                transfers.append({
                    "name": name,
                    "from_team": seen_teams[-1][1],
                    "from_season": seen_teams[-1][0],
                    "to_team": team,
                    "to_season": season,
                })
            seen_teams.append((season, team))

    transfers.sort(key=lambda x: x["to_season"])
    return transfers


def get_season_roster(season: str, team: str) -> list[dict]:
    """Get roster for a specific season and team."""
    rosters = load_rosters()
    if season not in rosters:
        return []
    # Try exact match first, then try normalized
    if team in rosters[season]:
        return rosters[season][team]
    # Reverse lookup
    for orig_team, players in rosters[season].items():
        if TEAM_NORMALIZE.get(orig_team, orig_team) == team:
            return players
    return []


def get_all_seasons() -> list[str]:
    """Get list of all seasons."""
    return sorted(load_rosters().keys())


def get_veteran_players(min_seasons: int = 3) -> list[dict]:
    """Find players who played at least N seasons."""
    records = build_career_table()
    player_seasons = defaultdict(set)
    player_info = {}

    for r in records:
        if not r.get("foreign", False):
            player_seasons[r["name"]].add(r["season"])
            player_info[r["name"]] = {
                "latest_team": r["team_current"],
                "latest_pos": r["pos"],
            }

    veterans = []
    for name, seasons in player_seasons.items():
        if len(seasons) >= min_seasons:
            info = player_info[name]
            veterans.append({
                "name": name,
                "seasons_played": len(seasons),
                "seasons": sorted(seasons),
                "latest_team": info["latest_team"],
                "latest_pos": info["latest_pos"],
            })

    veterans.sort(key=lambda x: x["seasons_played"], reverse=True)
    return veterans
