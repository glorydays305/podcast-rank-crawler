import argparse
import json
import os
from datetime import datetime
from dateutil import tz


def load_source(source_name: str):
    # 动态导入 scripts/sources/<source>.py
    import importlib
    return importlib.import_module(f"scripts.sources.{source_name}")


def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def now_str():
    cn = tz.gettz("Asia/Shanghai")
    return datetime.now(tz=cn).strftime("%Y-%m-%d %H:%M:%S %Z")


def render_markdown(items, title="中文播客热榜(自动抓取)"):
    lines = [f"# {title}", "", f"更新时间：{now_str()}", ""]
    lines.append("| 排名 | 播客 | 平台/\u6765源 | 链接 |")
    lines.append("|---:|---|---|---|")
    for i, it in enumerate(items, start=1):
        name = it.get("title", "").replace("|", " ")
        src = it.get("source", "unknown").replace("|", " ")
        link = it.get("url", "")
        lines.append(f"| {i} | {name} | {src} | [打开]({link}) |")
    lines.append("")
    return "\n".join(lines)


def render_html(items, title="中文播客热榜(自动抓取)"):
    # 简单静态页：表格 + 搜索
    from html import escape
    rows = "\n".join(
        f"""
        <tr>
          <td>{i}</td>
          <td>{escape(it.get("title",""))}</td>
          <td>{escape(it.get("source","unknown"))}</td>
          <td><a href=\"{escape(it.get("url",""))}\" target=\"_blank\" rel=\"noreferrer\">打开</a></td>
        </tr>
        """.strip()
        for i, it in enumerate(items, start=1)
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{escape(title)}</title>
  <style>
    body{{font-family: ui-sans-serif, system-ui, -apple-system; margin: 24px;}}
    .meta{{color:#666; margin: 8px 0 16px;}}
    input{{padding:10px 12px; width:min(520px, 100%); border:1px solid #ddd; border-radius:10px;}}
    table{{border-collapse: collapse; width: 100%; margin-top: 12px;}}
    th,td{{border-bottom:1px solid #eee; padding:10px; text-align:left;}}
    th{{position:sticky; top:0; background:#fff;}}
    .rank{{width:72px; text-align:right;}}
  </style>
</head>
<body>
  <h1>{escape(title)}</h1>
  <div class="meta">更新时间：{now_str()}</div>

  <input id="q" placeholder="搜索播客名称…" />

  <table>
    <thead>
      <tr><th class="rank">排名</th><th>播客</th><th>平台/\u6765源</th><th>链接</th></tr>
    </thead>
    <tbody id="tbody">
      {rows}
    </tbody>
  </table>

<script>
const q = document.getElementById('q');
const tbody = document.getElementById('tbody');
const rows = Array.from(tbody.querySelectorAll('tr'));
q.addEventListener('input', () => {{
  const k = q.value.trim().toLowerCase();
  rows.forEach(r => {{
    const text = r.innerText.toLowerCase();
    r.style.display = (!k || text.includes(k)) ? '' : 'none';
  }});
}});
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="scripts/sources 下的模块名，比如 demo_static")
    ap.add_argument("--out", required=True, help="输出目录，如 docs")
    args = ap.parse_args()

    src = load_source(args.source)
    items = src.fetch()

    # 标准化字段
    normalized = []
    for it in items:
        normalized.append({
            "title": it.get("title", "").strip(),
            "url": it.get("url", "").strip(),
            "source": it.get("source", args.source),
            "score": it.get("score"),   # 可选：热度分
            "tags": it.get("tags", []), # 可选
        })

    ensure_dir(args.out)
    ensure_dir("data")

    # 最新快照
    with open(os.path.join(args.out, "rank.json"), "w", encoding="utf-8") as f:
        json.dump({"updated_at": now_str(), "items": normalized}, f, ensure_ascii=False, indent=2)

    with open(os.path.join(args.out, "README.md"), "w", encoding="utf-8") as f:
        f.write(render_markdown(normalized))

    with open(os.path.join(args.out, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_html(normalized))

    # 历史：按日期存一份（便于做趋势）
    day = datetime.now(tz=tz.gettz("Asia/Shanghai")).strftime("%Y-%m-%d")
    with open(os.path.join("data", f"{day}.json"), "w", encoding="utf-8") as f:
        json.dump({"updated_at": now_str(), "items": normalized}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
