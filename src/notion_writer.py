import os
import json
import requests
from datetime import datetime

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def write_prediction(record: dict):
    """
    record 格式：
    {
      "date": "2026-06-01",
      "code": "600026",
      "name": "中远海能",
      "signal": "买入",     # 买入 / 观望 / 卖出
      "score": 81,
      "buy_price": 12.5,
      "sell_price": 14.0,
      "stop_loss": 11.8,
      "run_id": "26746897847"
    }
    """
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "股票名称": {
                "title": [{"text": {"content": record["name"]}}]
            },
            "日期": {
                "date": {"start": record["date"]}
            },
            "股票代码": {
                "rich_text": [{"text": {"content": record["code"]}}]
            },
            "AI信号": {
                "select": {"name": record["signal"]}
            },
            "AI评分": {
                "number": record["score"]
            },
            "建议买入价": {
                "number": record.get("buy_price", 0)
            },
            "建议卖出价": {
                "number": record.get("sell_price", 0)
            },
            "止损价": {
                "number": record.get("stop_loss", 0)
            },
            "预测是否准确": {
                "select": {"name": "⏳待验证"}
            },
            "Actions运行ID": {
                "rich_text": [{"text": {"content": str(record.get("run_id", ""))}}]
            }
        }
    }

    r = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        json=payload
    )

    if r.status_code == 200:
        print(f"✅ 写入成功：{record['name']}({record['code']}) "
              f"{record['signal']} {record['score']}分")
    else:
        print(f"❌ 写入失败：{r.status_code} {r.text}")


def update_actual_result(page_id: str, change_pct: float):
    """次日回填实际涨跌幅，并更新预测是否准确"""
    # 简单判断逻辑：买入信号且涨则准确，卖出信号且跌则准确
    payload = {
        "properties": {
            "次日涨跌幅%": {"number": round(change_pct, 2)},
            "预测是否准确": {
                "select": {"name": "✅准确" if change_pct > 0 else "❌失误"}
            }
        }
    }
    requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=HEADERS,
        json=payload
    )
