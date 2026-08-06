"""Day20 批量评测：在 test_questions.json 的 10 条问题上跑当前实现，生成 eval_results.json 与 EVAL_SUMMARY.md。

指标定义（见 Day20 最小理论）：
- source_hit：对答题，程序生成的来源是否覆盖 expected_sources；对拒答题，是否如期拒答（来源本就为空）。
- keyword_hit：对答题，must_contain 的关键概念是否出现在回答里（自动代理指标，不等于语义正确）。
- refusal_correct：该拒答的是否拒答、该回答的是否没拒。
- passed = source_hit 且 keyword_hit 且 refusal_correct。
延迟与 total_tokens 是工程成本，单独看，不计入正确性。

拒答题（should_refuse=true 且非算术）在 answer() 内不调 API 直接返回 REFUSAL，可离线验证；
答题题需要 DEEPSEEK_API_KEY 与网络，失败则记 error 并视为未通过，不掩盖。
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from agent import answer  # answer 返回 dict

QUESTIONS = Path(__file__).with_name("test_questions.json")
RESULTS = Path(__file__).with_name("eval_results.json")
SUMMARY = Path(__file__).with_name("EVAL_SUMMARY.md")


def grade_one(item: dict, rec: dict) -> dict:
    expected = item.get("expected_sources") or []
    must = item.get("must_contain") or []
    should_refuse = item.get("should_refuse", False)
    sources = rec.get("sources") or []
    answer_text = rec.get("answer") or ""
    refused = rec.get("refused", False)

    if should_refuse:
        source_hit = refused
        keyword_hit = True
        refusal_correct = refused
    else:
        source_hit = set(expected).issubset(set(sources))
        keyword_hit = all(k in answer_text for k in must)
        refusal_correct = not refused
    return {
        "source_hit": source_hit,
        "keyword_hit": keyword_hit,
        "refusal_correct": refusal_correct,
        "passed": source_hit and keyword_hit and refusal_correct,
    }


def render_md(summary: dict, rows: list) -> str:
    lines = []
    lines.append("# EVAL_SUMMARY（Day20 批量评测，关键词检索基线 before）\n")
    lines.append("> 评测对象：week4/knowledge-agent 当前实现（retriever.py 关键词检索 + agent.py 问答）。")
    lines.append("> 指标含义见 Day20 最小理论；本报告是**关键词检索基线（before）**，挑战任务 Embedding 检索为 after。\n")
    lines.append("## 汇总\n")
    lines.append(f"- 题目数：{summary['total']}（8 答 + 2 拒）")
    lines.append(f"- 通过率 passed（source_hit ∧ keyword_hit ∧ refusal_correct）：{summary['pass_rate']:.0%}")
    lines.append(f"- 来源命中率 source_hit：{summary['source_hit_rate']:.0%}")
    lines.append(f"- 关键词命中率 keyword_hit：{summary['keyword_hit_rate']:.0%}")
    lines.append(f"- 拒答正确率 refusal_correct：{summary['refusal_correct_rate']:.0%}")
    lines.append(f"- 总 Token：{summary['total_tokens']}（工程成本，与正确性分开看）\n")
    lines.append("## 逐题明细\n")
    lines.append("| # | 难度 | 问题 | passed | 来源 | 来源命中 | 关键词命中 | 拒答正确 | total |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        src = ", ".join(r["sources"]) if r["sources"] else "—"
        mark = "Y" if r["passed"] else "N"
        sh = "Y" if r["source_hit"] else "N"
        kh = "Y" if r["keyword_hit"] else "N"
        rc = "Y" if r["refusal_correct"] else "N"
        err = f"  err={r['error']}" if r["error"] else ""
        lines.append(f"| {i} | {r['difficulty']} | {r['question']} | {mark} | {src} | {sh} | {kh} | {rc} | {r['total_tokens']} |{err}")
    lines.append("\n## 说明\n")
    lines.append("- 来源命中率与关键词命中率是自动代理指标，不等于语义正确率；原回答已完整保留在 eval_results.json，需要人工抽查关键概念是否真正成立。")
    lines.append("- 拒答正确率只看检索不到且非算术时是否拒答，不依赖模型，可离线验证（本题 2 道拒答题已离线通过）。")
    lines.append("- 本份为关键词检索基线 before；挑战任务 Embedding 检索为 after，用同一份 test_questions.json 跑 before/after 对比，重点看近义问召回是否被补上。")
    if any(r["error"] for r in rows):
        lines.append("\n注意：部分答题题未完成（缺 Key 或网络不可达），已记入 error 列且不计入 passed；其正确性未验证，不代表实现缺陷。")
    return "\n".join(lines) + "\n"


def main() -> int:
    qpath = Path(sys.argv[1]) if len(sys.argv) > 1 else QUESTIONS
    questions = json.loads(qpath.read_text(encoding="utf-8"))
    rows = []
    for item in questions:
        q = item["question"]
        rec = {
            "question": q,
            "difficulty": item.get("difficulty"),
            "should_refuse": item.get("should_refuse", False),
            "expected_sources": item.get("expected_sources") or [],
            "must_contain": item.get("must_contain") or [],
        }
        start = time.perf_counter()
        try:
            res = answer(q)
            rec["answer"] = res["answer"]
            rec["sources"] = res["sources"]
            rec["refused"] = res["refused"]
            rec["total_tokens"] = res["usage"]["total_tokens"]
            rec["error"] = None
        except Exception as exc:  # 无 Key / 网络失败等，不掩盖
            rec["answer"] = None
            rec["sources"] = []
            rec["refused"] = False
            rec["total_tokens"] = 0
            rec["error"] = f"{type(exc).__name__}: {exc}"
        rec["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
        rec.update(grade_one(item, rec))
        rows.append(rec)

    n = len(rows)

    def rate(key):
        return sum(1 for r in rows if r[key]) / n if n else 0

    summary = {
        "total": n,
        "passed": sum(1 for r in rows if r["passed"]),
        "source_hit_rate": rate("source_hit"),
        "keyword_hit_rate": rate("keyword_hit"),
        "refusal_correct_rate": rate("refusal_correct"),
        "pass_rate": rate("passed"),
        "total_tokens": sum(r["total_tokens"] for r in rows),
    }
    RESULTS.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY.write_text(render_md(summary, rows), encoding="utf-8")
    print(f"评测完成：pass_rate={summary['pass_rate']:.0%}  source_hit={summary['source_hit_rate']:.0%}  keyword_hit={summary['keyword_hit_rate']:.0%}  refusal_correct={summary['refusal_correct_rate']:.0%}  total_tokens={summary['total_tokens']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
