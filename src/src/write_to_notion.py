import os
import json
import glob
from notion_writer import write_prediction

# 读取分析输出的JSON结果文件
# daily_stock_analysis 会把结果存在 output/ 或 results/ 目录
result_files = glob.glob("output/results/*.json") or glob.glob("results/*.json")

run_id = os.environ.get("GITHUB_RUN_ID", "unknown")

for file_path in result_files:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 提取关键字段（根据实际JSON结构调整）
    record = {
        "date": data.get("analysis_date", ""),
        "code": data.get("stock_code", ""),
        "name": data.get("stock_name", ""),
        "signal": data.get("decision", {}).get("action", "观望"),
        "score": data.get("decision", {}).get("score", 0),
        "buy_price": data.get("decision", {}).get("buy_price", 0),
        "sell_price": data.get("decision", {}).get("sell_price", 0),
        "stop_loss": data.get("decision", {}).get("stop_loss", 0),
        "run_id": run_id
    }
    
    write_prediction(record)
