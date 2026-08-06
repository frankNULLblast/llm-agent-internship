"""模型对比实验：同一份 test_questions.json，分别用多个模型跑一遍，比正确性与工程成本。

用法：
    python compare_models.py                                  # 默认对比 flash 与 pro
    python compare_models.py deepseek-v4-flash deepseek-v4-pro
    python compare_models.py deepseek-v4-flash deepseek-v4-pro --questions test_questions.json

为什么不改 agent.py：agent.answer() 在调用时才 os.getenv("DEEPSEEK_MODEL")，
所以运行期设置环境变量即可切换被测模型，实现零侵入对比。

评分口径与 Day20 eval.py 完全一致（复用 grade_one），保证 before/after 可比。
拒答题在 answer() 内不调 API 直接返回，两模型必然同分、token 为 0——
这说明"拒答能力由检索层决定，与模型无关"，是对比中要讲清楚的结论。
"""

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from eval import grade_one  # 复用 Day20 评分口径，避免两套标准
from agent import answer

QUESTIONS = Path(__file__).with_name("test_questions.json")
RESULTS = Path(__file__).with_name("model_compare.json")
REPORT = Path(__file__).with_name("MODEL_COMPARE.md")

DEFAULT_MODELS = ["deepseek-v4-flash", "deepseek-v4-pro"]


def run_one_model(model: str, questions: list) -> dict:
    """在指定模型下跑完整题集，返回逐题结果与汇总。"""
    os.environ["DEEPSEEK_MODEL"] = model
    rows = []
    for item in questions:
        q = item["question"]
        rec = {
            "question": q,
            "difficulty": item.get("difficulty"),
            "should_refuse": item.get("should_refuse", False),
        }
        start = time.perf_counter()
        try:
            res = answer(q)
            rec["answer"] = res["answer"]
            rec["sources"] = res["sources"]
            rec["refused"] = res["refused"]
            rec["total_tokens"] = res["usage"]["total_tokens"]
            rec["error"] = None
        except Exception as exc:  # 缺 Key / 网络失败 / 模型名无效，不掩盖
            rec["answer"] = None
            rec["sources"] = []
            rec["refused"] = False
            rec["total_tokens"] = 0
            rec["error"] = f"{type(exc).__name__}: {exc}"
        rec["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
        rec.update(grade_one(item, rec))
        rows.append(rec)
        flag = "Y" if rec["passed"] else "N"
        print(f"  [{model}] {flag} {rec['latency_ms']:>7.1f}ms tok={rec['total_tokens']:<5} {q[:26]}")

    n = len(rows) or 1
    api_rows = [r for r in rows if r["total_tokens"] > 0]  # 真正调了 API 的题
    summary = {
        "model": model,
        "total": len(rows),
        "passed": sum(1 for r in rows if r["passed"]),
        "pass_rate": sum(1 for r in rows if r["passed"]) / n,
        "source_hit_rate": sum(1 for r in rows if r["source_hit"]) / n,
        "keyword_hit_rate": sum(1 for r in rows if r["keyword_hit"]) / n,
        "refusal_correct_rate": sum(1 for r in rows if r["refusal_correct"]) / n,
        "total_tokens": sum(r["total_tokens"] for r in rows),
        "avg_latency_ms": round(sum(r["latency_ms"] for r in rows) / n, 1),
        "api_avg_latency_ms": round(
            sum(r["latency_ms"] for r in api_rows) / len(api_rows), 1
        ) if api_rows else 0.0,
        "errors": sum(1 for r in rows if r["error"]),
    }
    return {"summary": summary, "rows": rows}


def render_md(reports: list) -> str:
    L = []
    L.append("# MODEL_COMPARE：同题集多模型对比\n")
    L.append("> 同一份 `test_questions.json`、同一套检索与 Prompt，只换 `DEEPSEEK_MODEL`。")
    L.append("> 评分口径复用 Day20 `eval.py` 的 `grade_one`，与基线报告可直接比对。\n")

    L.append("## 汇总对比\n")
    L.append("| 模型 | 通过率 | 来源命中 | 关键词命中 | 拒答正确 | 总 Token | 调用均延迟 | 失败数 |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in reports:
        s = r["summary"]
        L.append(
            f"| `{s['model']}` | {s['pass_rate']:.0%} ({s['passed']}/{s['total']}) "
            f"| {s['source_hit_rate']:.0%} | {s['keyword_hit_rate']:.0%} | {s['refusal_correct_rate']:.0%} "
            f"| {s['total_tokens']} | {s['api_avg_latency_ms']:.0f} ms | {s['errors']} |"
        )

    L.append("\n## 逐题对比（passed / token / 延迟）\n")
    head = "| # | 难度 | 问题 | " + " | ".join(f"`{r['summary']['model']}`" for r in reports) + " |"
    L.append(head)
    L.append("|---|---|---|" + "---|" * len(reports))
    base = reports[0]["rows"]
    for i in range(len(base)):
        q = base[i]["question"]
        diff = base[i]["difficulty"]
        cells = []
        for r in reports:
            row = r["rows"][i]
            mark = "Y" if row["passed"] else "N"
            cells.append(f"{mark} / {row['total_tokens']}tok / {row['latency_ms']:.0f}ms")
        L.append(f"| {i+1} | {diff} | {q} | " + " | ".join(cells) + " |")

    L.append("\n## 差异题（结论最集中的地方）\n")
    diffs = []
    for i in range(len(base)):
        marks = {r["summary"]["model"]: r["rows"][i]["passed"] for r in reports}
        if len(set(marks.values())) > 1:
            diffs.append((i, marks))
    if diffs:
        for i, marks in diffs:
            L.append(f"\n### 第 {i+1} 题：{base[i]['question']}\n")
            for r in reports:
                row = r["rows"][i]
                L.append(f"- **{r['summary']['model']}** → passed={row['passed']}，来源={row['sources'] or '—'}")
                L.append(f"  - 回答：{(row['answer'] or '(无)')[:180]}")
    else:
        L.append("本轮所有题目两模型判定一致，正确性未拉开差距。")
        L.append("这本身是有效结论：**当检索质量足够时，题目难度不足以区分模型能力**，")
        L.append("差异主要落在工程成本（token 与延迟）上，而非答案对错。")

    L.append("\n## 怎么读这张表\n")
    L.append("- **拒答题两模型必然同分且 token=0**：拒答发生在检索层（检索为空且非算术即拒），压根没到模型，所以拒答正确率不体现模型差异。")
    L.append("- **通过率相同不等于两模型一样**：还要看 token 成本与延迟；同样答对，便宜快的更适合线上。")
    L.append("- **keyword_hit 是代理指标**：只查关键词是否出现，不代表语义正确，差异题需人工读原答案（已存于 `model_compare.json`）。")
    L.append("- 想让对比更有区分度，就往 `test_questions.json` 里加多跳推理题、易混淆题，而不是加更多简单事实题。")
    return "\n".join(L) + "\n"


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    qpath = QUESTIONS
    if "--questions" in sys.argv:
        qpath = Path(sys.argv[sys.argv.index("--questions") + 1])
        args = [a for a in args if a != str(qpath)]
    models = args or DEFAULT_MODELS

    if not os.getenv("DEEPSEEK_API_KEY"):
        print("错误：未设置 DEEPSEEK_API_KEY（先 source .env）", file=sys.stderr)
        return 2

    questions = json.loads(qpath.read_text(encoding="utf-8"))
    print(f"题目数 {len(questions)}，对比模型：{', '.join(models)}\n")

    reports = []
    for m in models:
        print(f"--- 正在跑 {m} ---")
        reports.append(run_one_model(m, questions))
        print()

    RESULTS.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT.write_text(render_md(reports), encoding="utf-8")

    print("=== 对比结果 ===")
    for r in reports:
        s = r["summary"]
        print(
            f"{s['model']:<22} pass={s['pass_rate']:.0%}  "
            f"tokens={s['total_tokens']:<6} api_avg_latency={s['api_avg_latency_ms']:.0f}ms  errors={s['errors']}"
        )
    print(f"\n已生成：{REPORT.name} / {RESULTS.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
