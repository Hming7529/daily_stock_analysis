import os
import json
import glob
import sys

# 把 src 目录加入路径，才能 import notion_writer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notion_writer import write_prediction

run_id = os.environ.get("GITHUB_RUN_ID", "unknown")

# 这个项目把报告输出在 reports/ 目录，格式是 .md 文件
# 同时会输出 JSON 结构到 data/ 目录
result_files = (
    glob.glob("data/analysis_results*.json") +
    glob.glob("data/*result*.json") +
    glob.glob("reports/*.json")
)

if not result_files:
    print("⚠️ 未找到分析结果JSON文件，尝试解析reports目录的md文件...")
    # 如果没有JSON，说明今天可能没有分析结果（非交易日等）
    print("ℹ️ 无可写入数据，跳过 Notion 写入")
    sys.exit(0)

success_count = 0
for file_path in result_files:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 兼容两种可能的JSON结构
        # 结构1：单只股票的分析结果
        if "stock_code" in data:
            stocks = [data]
        # 结构2：多只股票的列表
        elif "results" in data:
            stocks = data["results"]
        elif isinstance(data, list):
            stocks = data
        else:
            stocks = [data]

        for stock in stocks:
            decision = stock.get("decision", {})
            record = {
                "date": stock.get("analysis_date", stock.get("date", "")),
                "code": stock.get("stock_code", stock.get("code", "")),
                "name": stock.get("stock_name", stock.get("name", "")),
                "signal": decision.get("action", decision.get("signal", "观望")),
                "score": decision.get("score", decision.get("rating", 0)),
                "buy_price": decision.get("buy_price", decision.get("entry_price", 0)),
                "sell_price": decision.get("sell_price", decision.get("target_price", 0)),
                "stop_loss": decision.get("stop_loss", decision.get("stop_price", 0)),
                "run_id": run_id
            }

            # 过滤掉无效记录
            if not record["code"] or not record["name"]:
                continue

            write_prediction(record)
            success_count += 1

    except Exception as e:
        print(f"❌ 处理文件 {file_path} 出错: {e}")
        continue

print(f"\n✅ 共写入 {success_count} 条记录到 Notion")
