"""資料清洗與前處理（防禦性處理缺失欄位）"""
import json
import pandas as pd
from config.settings import RAW_DIR, PROCESSED_DIR, STAT_COLUMNS, OPPONENT_NAME_MAP, PLAYOFF_TAGS
from scraper.utils import parse_stat_pair, parse_pct


def load_raw_players() -> pd.DataFrame:
    with open(RAW_DIR / "players.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    players = data.get("球員", data) if isinstance(data, dict) else data
    for p in players:
        p.pop("逐場數據", None)
        p.pop("累計數據", None)
    return pd.DataFrame(players) if players else pd.DataFrame()


def load_raw_matches() -> pd.DataFrame:
    with open(RAW_DIR / "match_records.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data) if data else pd.DataFrame()


def clean_players(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        print("  ⚠️  球員資料為空")
        return df
    df = df.copy()

    # 生日（可能不存在於球隊頁面，但個人頁面有）
    if "生日" in df.columns:
        df["生日"] = pd.to_datetime(df["生日"], errors="coerce")
        df["年齡"] = (pd.Timestamp.now() - df["生日"]).dt.days // 365

    # 隊長
    if "備註" in df.columns:
        df["是否隊長"] = df["備註"].fillna("").str.contains("隊長")
    else:
        df["是否隊長"] = False

    # BMI
    if "身高(cm)" in df.columns and "體重(kg)" in df.columns:
        h = pd.to_numeric(df["身高(cm)"], errors="coerce") / 100
        w = pd.to_numeric(df["體重(kg)"], errors="coerce")
        df["BMI"] = (w / (h ** 2)).round(1)

    if "背號" in df.columns:
        df.sort_values("背號", inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


def clean_matches(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        print("  ⚠️  比賽紀錄為空")
        return df
    df = df.copy()

    if "比賽日期" in df.columns:
        df["比賽日期"] = pd.to_datetime(df["比賽日期"], errors="coerce")

    # Normalize opponent names (historical → current)
    if "對手" in df.columns:
        # Direct mapping
        df["對手"] = df["對手"].replace(OPPONENT_NAME_MAP)
        # Handle playoff tags like "挑戰賽1", "挑戰賽2" → mark as playoff
        df["賽事類型"] = "例行賽"
        for tag in PLAYOFF_TAGS:
            mask = df["對手"].str.contains(tag, na=False)
            df.loc[mask, "賽事類型"] = "季後賽"
            # Try to extract actual opponent from context (same date)
            # For now, keep as-is but tag it
        # Also strip trailing numbers from opponent (e.g. "挑戰賽1" stays but is tagged)

    for col in STAT_COLUMNS:
        if col in df.columns:
            parsed = df[col].apply(parse_stat_pair)
            df[f"{col}_成功"] = parsed.apply(lambda x: x[0])
            df[f"{col}_總數"] = parsed.apply(lambda x: x[1])

        pct_col = f"{col}%"
        if pct_col in df.columns:
            df[pct_col] = df[pct_col].apply(parse_pct)

    if "得分" in df.columns:
        df["得分"] = pd.to_numeric(df["得分"], errors="coerce").fillna(0).astype(int)

    if "球員背號" in df.columns:
        df.sort_values(["球員背號", "比賽日期"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


def build_player_stats_summary(matches_clean: pd.DataFrame) -> pd.DataFrame:
    if matches_clean.empty:
        return pd.DataFrame()

    agg = {}
    for col in STAT_COLUMNS:
        for suffix in ["_成功", "_總數"]:
            c = f"{col}{suffix}"
            if c in matches_clean.columns:
                agg[c] = "sum"
    if "得分" in matches_clean.columns:
        agg["得分"] = "sum"

    if not agg:
        return pd.DataFrame()

    group_cols = [c for c in ["player_id", "球員背號", "球員姓名", "球隊"] if c in matches_clean.columns]
    if not group_cols:
        return pd.DataFrame()

    summary = matches_clean.groupby(group_cols).agg(
        出賽場次=("比賽日期", "count"),
        **{k: pd.NamedAgg(column=k, aggfunc=v) for k, v in agg.items()}
    ).reset_index()

    for col in STAT_COLUMNS:
        s_col, t_col = f"{col}_成功", f"{col}_總數"
        if s_col in summary.columns and t_col in summary.columns:
            summary[f"{col}%"] = (
                summary[s_col] / summary[t_col].replace(0, float("nan")) * 100
            ).round(2)

    return summary


def clean_all():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 球員
    players = load_raw_players()
    players_clean = clean_players(players)
    out_p = PROCESSED_DIR / "players_clean.csv"
    players_clean.to_csv(out_p, index=False, encoding="utf-8-sig")
    print(f"  ✅ 球員資料：{len(players_clean)} 筆 → {out_p.name}")

    # 比賽
    matches = load_raw_matches()
    matches_clean = clean_matches(matches)
    out_m = PROCESSED_DIR / "matches_clean.csv"
    matches_clean.to_csv(out_m, index=False, encoding="utf-8-sig")
    print(f"  ✅ 比賽紀錄：{len(matches_clean)} 筆 → {out_m.name}")

    # 彙總
    summary = build_player_stats_summary(matches_clean)
    out_s = PROCESSED_DIR / "player_stats_summary.csv"
    summary.to_csv(out_s, index=False, encoding="utf-8-sig")
    print(f"  ✅ 球員彙總：{len(summary)} 筆 → {out_s.name}")


if __name__ == "__main__":
    clean_all()
