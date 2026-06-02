import os
import re
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notion_writer import write_prediction

run_id = os.environ.get("GITHUB_RUN_ID", "unknown")

def parse_report(content):
    results = []

    # 提取日期
    date_match = re.search(r'# 🎯 (\d{4}-\d{2}-\d{2})', content)
    date = date_match.group(1) if date_match else ""

    # 按股票章节切割
    sections = re.split(r'\n(?=## .+?\(\d+\))', content)

    # 从摘要行提取信号和评分
    summary_map = {}
    for m in re.finditer(
        r'[🟢🟡⚪🔴]\s+\*\*(.+?)\((\w+)\)\*\*:\s*(\S+)\s*\|\s*评分\s*(\d+)\s*\|\s*(\S+)',
        content
    ):
        name, code, signal, score, sentiment = m.groups()
        summary_map[code] = {
            "name": name,
            "signal": signal,
            "score": int(score),
            "sentiment": sentiment
        }

    # 从每个章节提取操作点位
    for section in sections:
        code_match = re.search(r'## .+?\((\w+)\)', section)
        if not code_match:
            continue
        code = code_match.group(1)
        if code not in summary_map:
            continue

        buy_match  = re.search(r'理想买入点\s*\|\s*([\d.]+)元', section)
        sell_match = re.search(r'目标位\s*\|\s*([\d.]+)元', section)
        stop_match = re.search(r'止损位\s*\|\s*([\d.]+)元', section)

        signal_map = {
            "买入": "买入", "持有": "持有",
            "观望": "观望", "卖出": "卖出", "减仓": "卖出"
        }
        info = summary_map[code]

        results.append({
            "date":       date,
            "code":       code,
            "name":       info["name"],
            "signal":     signal_map.get(info["signal"], "观望"),
            "score":      info["score"],
            "sentiment":  info["sentiment"],
            "buy_price":  float(buy_match.group(1))  if buy_match  else 0,
            "sell_price": float(sell_match.group(1)) if sell_match else 0,
            "stop_loss":  float(stop_match.group(1)) if stop_match else 0,
            "run_id":     run_id
        })

    return results


# 查找报告文件
report_files = sorted(glob.glob("reports/report_*.md"))

if not report_files:
    print("⚠️ 未找到报告文件，跳过写入")
    sys.exit(0)

# 取最新一份报告
latest = report_files[-1]
print(f"📄 正在解析报告: {latest}")

with open(latest, "r", encoding="utf-8") as f:
    content = f.read()

records = parse_report(content)

if not records:
    print("⚠️ 未解析到有效记录，跳过写入")
    sys.exit(0)

success = 0
for record in records:
    try:
        write_prediction(record)
        success += 1
    except Exception as e:
        print(f"❌ 写入失败 {record['name']}: {e}")

print(f"\n✅ 共写入 {success}/{len(records)} 条记录到 Notion")
