"""
臺北鯨華女子排球隊 — 球員分析專案
主程式入口：依序執行完整分析流程

使用方式:
    python main.py                             # 爬取全聯盟 + 全部步驟
    python main.py --team 臺北鯨華             # 只爬單隊
    python main.py --steps scrape clean        # 只執行爬蟲 + 清洗
    python main.py --steps dashboard           # 啟動 Streamlit 儀表板
"""
import argparse
import subprocess
import sys
from config.settings import RAW_DIR, PROCESSED_DIR, FIGURES_DIR, REPORTS_DIR, WOMEN_TEAMS


ALL_STEPS = ["scrape", "clean", "analyze", "visualize", "ml", "dashboard"]


def run_pipeline(steps: list[str], team: str = None):
    """執行指定的分析步驟"""

    print("🏐 TVL 企業排球聯賽 — 女子組球員分析專案")
    print("=" * 55)

    if "scrape" in steps:
        print("\n🕷️  [1/6] 爬蟲抓取資料...")
        from scraper.run_scraper import run
        run(team_name=team)

    if "clean" in steps:
        print("\n🧹 [2/6] 資料清洗與前處理...")
        from analysis.data_cleaning import clean_all
        clean_all()

    if "analyze" in steps:
        print("\n📊 [3/6] 數據分析...")
        from analysis.descriptive_stats import run_stats
        from analysis.match_analysis import run_match_analysis
        run_stats()
        run_match_analysis()

    if "visualize" in steps:
        print("\n📈 [4/6] 產生視覺化圖表...")
        from visualization.player_profiles import generate_profiles
        from visualization.team_charts import generate_team_charts
        from visualization.match_trends import generate_match_trends
        generate_profiles()
        generate_team_charts()
        generate_match_trends()

    if "ml" in steps:
        print("\n🤖 [5/6] 機器學習建模...")
        from ml.train import train_all
        train_all()

    if "dashboard" in steps:
        print("\n🖥️  [6/6] 啟動 Streamlit 儀表板...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard/app.py"])
        return

    non_dash = [s for s in steps if s != "dashboard"]
    if non_dash:
        print("\n" + "=" * 55)
        print("✅ 全部流程完成！輸出位置：")
        print(f"   📁 原始資料：  {RAW_DIR}")
        print(f"   📁 處理後資料：{PROCESSED_DIR}")
        print(f"   📁 分析報告：  {REPORTS_DIR}")
        print(f"   📁 圖表：      {FIGURES_DIR}")
        print(f"\n💡 啟動儀表板：python main.py --steps dashboard")


def main():
    parser = argparse.ArgumentParser(
        description="TVL 企排女子組分析專案",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
範例:
  python main.py                             全聯盟全部執行
  python main.py --team 臺北鯨華             只爬單隊
  python main.py --steps scrape clean        爬蟲 + 清洗
  python main.py --steps dashboard           啟動互動儀表板

可用隊伍：{', '.join(WOMEN_TEAMS.keys())}
        """,
    )
    parser.add_argument(
        "--steps", nargs="+", default=["scrape", "clean", "analyze", "visualize", "ml"],
        choices=ALL_STEPS, help="要執行的步驟",
    )
    parser.add_argument(
        "--team", type=str, default=None,
        help="指定隊伍名稱（預設：全聯盟）",
    )
    args = parser.parse_args()
    run_pipeline(args.steps, team=args.team)


if __name__ == "__main__":
    main()
