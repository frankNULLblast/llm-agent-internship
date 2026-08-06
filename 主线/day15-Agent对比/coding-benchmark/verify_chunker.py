"""minichunk 提交物自动验收脚本。

用法:
    python verify_chunker.py <提交目录> [--label 模型名]

<提交目录> 下应能直接 import 到 minichunk 包, 即目录结构形如:
    <提交目录>/minichunk/__init__.py

脚本对提交跑 15 项契约检查, 输出加权得分与明细, 并写出 verify_result.json。
只用标准库, 不改动被测代码。
"""

from __future__ import annotations

import argparse
import ast
import importlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field, asdict
from pathlib import Path

# ---------------------------------------------------------------- 测试语料

MD_DOC = """# 安装
安装前请确认环境。

## Windows
使用 winget 安装即可。

## Linux
使用 apt 安装即可。

# 使用
调用 split 方法。
"""

MIXED_DOC = (
    "这是第一句话。This is the second sentence! 第三句在这里吗？"
    "Yes it is. 最后一句结束了；真的结束了。"
)

PLAIN_DOC = "".join(f"第{i}段内容ABCDEFG " for i in range(1, 40))


@dataclass
class Check:
    cid: str
    name: str
    weight: int
    passed: bool = False
    detail: str = ""


@dataclass
class Report:
    label: str = ""
    submission: str = ""
    checks: list = field(default_factory=list)
    score: float = 0.0
    max_score: int = 0
    percent: float = 0.0


# ---------------------------------------------------------------- 工具

def _offsets_ok(text: str, chunks) -> tuple[bool, str]:
    """校验每个 chunk 的 start/end 能在原文精确切回。"""
    if not chunks:
        return False, "未返回任何 chunk"
    for i, c in enumerate(chunks):
        try:
            s, e, t = c.start, c.end, c.text
        except AttributeError as exc:
            return False, f"chunk[{i}] 缺少属性: {exc}"
        if not isinstance(s, int) or not isinstance(e, int):
            return False, f"chunk[{i}] start/end 不是 int"
        if text[s:e] != t:
            got = text[s:e]
            return False, (
                f"chunk[{i}] 偏移错位: text[{s}:{e}]={got[:30]!r} "
                f"!= chunk.text={t[:30]!r}"
            )
    return True, f"{len(chunks)} 个 chunk 偏移全部可回切"


def _strip_ws(s: str) -> str:
    return "".join(s.split())


def _raises_value_error(fn) -> bool:
    """构造时或 split 时抛 ValueError 都算通过。"""
    try:
        obj = fn()
    except ValueError:
        return True
    except Exception:
        return False
    try:
        obj.split("一些文本内容")
    except ValueError:
        return True
    except Exception:
        return False
    return False


# ---------------------------------------------------------------- 各项检查

def run_checks(sub_dir: Path, label: str) -> Report:
    rep = Report(label=label, submission=str(sub_dir))
    checks: list[Check] = []

    def add(cid, name, weight, passed, detail=""):
        checks.append(Check(cid, name, weight, passed, detail))

    sys.path.insert(0, str(sub_dir))
    for mod in [m for m in sys.modules if m == "minichunk" or m.startswith("minichunk.")]:
        del sys.modules[mod]

    # C01 可导入且暴露三个公开名字
    mc = None
    try:
        mc = importlib.import_module("minichunk")
        missing = [n for n in ("Chunk", "get_chunker", "register") if not hasattr(mc, n)]
        add("C01", "包可导入且暴露 Chunk/get_chunker/register", 1,
            not missing, "缺少: " + ", ".join(missing) if missing else "OK")
    except Exception as exc:
        add("C01", "包可导入且暴露 Chunk/get_chunker/register", 1, False, f"导入失败: {exc!r}")
        rep.checks = [asdict(c) for c in checks]
        rep.max_score = 19
        return rep

    get_chunker = getattr(mc, "get_chunker", None)
    register = getattr(mc, "register", None)

    # C02 fixed 可构造, Chunk 四字段齐全
    fixed_chunks = None
    try:
        ch = get_chunker("fixed", chunk_size=40, overlap=10)
        fixed_chunks = ch.split(PLAIN_DOC)
        c0 = fixed_chunks[0]
        lack = [a for a in ("text", "start", "end", "meta") if not hasattr(c0, a)]
        add("C02", "Chunk 具备 text/start/end/meta 四字段", 1,
            not lack, "缺少: " + ", ".join(lack) if lack else "OK")
    except Exception as exc:
        add("C02", "Chunk 具备 text/start/end/meta 四字段", 1, False, f"{exc!r}")

    # C03 fixed 无重叠时拼接可还原全文
    try:
        seq = get_chunker("fixed", chunk_size=40, overlap=0).split(PLAIN_DOC)
        joined = "".join(c.text for c in seq)
        ok = joined == PLAIN_DOC
        add("C03", "fixed(overlap=0) 拼接可完整还原原文", 1, ok,
            "OK" if ok else f"拼接长度 {len(joined)} vs 原文 {len(PLAIN_DOC)}")
    except Exception as exc:
        add("C03", "fixed(overlap=0) 拼接可完整还原原文", 1, False, f"{exc!r}")

    # C04 overlap 真实生效
    try:
        ok = False
        detail = "chunk 数不足, 无法判定"
        if fixed_chunks and len(fixed_chunks) >= 2:
            a, b = fixed_chunks[0], fixed_chunks[1]
            actual = a.end - b.start
            ok = actual == 10
            detail = f"相邻块重叠 {actual} 字符 (期望 10)"
        add("C04", "fixed 的 overlap 参数真实生效", 1, ok, detail)
    except Exception as exc:
        add("C04", "fixed 的 overlap 参数真实生效", 1, False, f"{exc!r}")

    # C05 偏移可回切 - fixed   [核心]
    try:
        ok, detail = _offsets_ok(PLAIN_DOC, fixed_chunks)
        add("C05", "★ 偏移可回切 (fixed)", 2, ok, detail)
    except Exception as exc:
        add("C05", "★ 偏移可回切 (fixed)", 2, False, f"{exc!r}")

    # C06 偏移可回切 - sentence   [核心]
    sent_chunks = None
    try:
        ch = get_chunker("sentence", max_chars=30)
        sent_chunks = ch.split(MIXED_DOC)
        ok, detail = _offsets_ok(MIXED_DOC, sent_chunks)
        add("C06", "★ 偏移可回切 (sentence)", 2, ok, detail)
    except Exception as exc:
        add("C06", "★ 偏移可回切 (sentence)", 2, False, f"{exc!r}")

    # C07 偏移可回切 - markdown   [核心]
    md_chunks = None
    try:
        ch = get_chunker("markdown")
        md_chunks = ch.split(MD_DOC)
        ok, detail = _offsets_ok(MD_DOC, md_chunks)
        add("C07", "★ 偏移可回切 (markdown)", 2, ok, detail)
    except Exception as exc:
        add("C07", "★ 偏移可回切 (markdown)", 2, False, f"{exc!r}")

    # C08 中英混排句子切分
    try:
        ok = False
        detail = "未产出 chunk"
        if sent_chunks:
            n = len(sent_chunks)
            joined = _strip_ws("".join(c.text for c in sent_chunks))
            no_loss = joined == _strip_ws(MIXED_DOC)
            ok = n >= 3 and no_loss
            detail = f"切出 {n} 块, 字符{'无' if no_loss else '有'}丢失"
        add("C08", "sentence 正确处理中英混排且不丢字符", 1, ok, detail)
    except Exception as exc:
        add("C08", "sentence 正确处理中英混排且不丢字符", 1, False, f"{exc!r}")

    # C09 markdown heading_path 维护层级
    try:
        ok = False
        detail = "未找到二级标题路径"
        if md_chunks:
            paths = []
            for c in md_chunks:
                p = (c.meta or {}).get("heading_path")
                if isinstance(p, (list, tuple)):
                    paths.append(list(p))
            has_two = any(len(p) == 2 and p[0] == "安装" for p in paths)
            has_reset = any(p == ["使用"] for p in paths)
            ok = has_two and has_reset
            detail = f"heading_path 样本: {paths[:5]}"
        add("C09", "markdown 的 heading_path 正确维护层级", 1, ok, detail)
    except Exception as exc:
        add("C09", "markdown 的 heading_path 正确维护层级", 1, False, f"{exc!r}")

    # C10 参数校验
    try:
        r1 = _raises_value_error(lambda: get_chunker("fixed", chunk_size=0, overlap=0))
        r2 = _raises_value_error(lambda: get_chunker("fixed", chunk_size=10, overlap=10))
        r3 = _raises_value_error(lambda: get_chunker("fixed", chunk_size=10, overlap=-1))
        ok = r1 and r2 and r3
        add("C10", "非法参数抛 ValueError", 1, ok,
            f"chunk_size<=0:{r1} overlap>=size:{r2} overlap<0:{r3}")
    except Exception as exc:
        add("C10", "非法参数抛 ValueError", 1, False, f"{exc!r}")

    # C11 空输入
    try:
        results = []
        for name, kw in (("fixed", {"chunk_size": 20, "overlap": 5}),
                         ("sentence", {"max_chars": 20}),
                         ("markdown", {})):
            results.append(get_chunker(name, **kw).split("") == [])
        ok = all(results)
        add("C11", "空输入返回 [] 且不抛异常", 1, ok, f"三策略结果: {results}")
    except Exception as exc:
        add("C11", "空输入返回 [] 且不抛异常", 1, False, f"{exc!r}")

    # C12 插件注册不改源码   [核心]
    try:
        @register("_probe_strategy_")
        class _Probe:  # noqa: D401
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def split(self, text):
                return ["PROBE_OK"]

        got = get_chunker("_probe_strategy_").split("任意文本")
        ok = got == ["PROBE_OK"]
        add("C12", "★ 第三方策略可注册且无需改包内代码", 2, ok, f"返回: {got!r}")
    except Exception as exc:
        add("C12", "★ 第三方策略可注册且无需改包内代码", 2, False, f"{exc!r}")

    # C13 未知策略报错
    try:
        ok = False
        detail = "未抛异常"
        try:
            get_chunker("definitely_not_exist")
        except (KeyError, ValueError) as exc:
            ok, detail = True, f"抛出 {type(exc).__name__}"
        except Exception as exc:
            detail = f"抛出非预期异常 {type(exc).__name__}"
        add("C13", "未知策略抛 KeyError/ValueError", 1, ok, detail)
    except Exception as exc:
        add("C13", "未知策略抛 KeyError/ValueError", 1, False, f"{exc!r}")

    # C14 CLI 可用且输出合法 JSON
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                         encoding="utf-8") as fp:
            fp.write(PLAIN_DOC)
            tmp_path = fp.name
        # 统一子进程 IO 编码, 避免 Windows 控制台默认 GBK 造成的误判
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        proc = subprocess.run(
            [sys.executable, "-m", "minichunk", "--strategy", "fixed",
             "--file", tmp_path, "--chunk-size", "50", "--overlap", "10", "--json"],
            cwd=str(sub_dir), capture_output=True, text=True, timeout=30,
            encoding="utf-8", env=env,
        )
        ok, detail = False, f"退出码 {proc.returncode}"
        if proc.returncode == 0:
            try:
                data = json.loads(proc.stdout)
                fields_ok = bool(data) and all(
                    all(k in item for k in ("text", "start", "end", "meta"))
                    for item in data
                )
                ok = fields_ok
                detail = f"输出 {len(data)} 条 JSON, 字段{'齐全' if fields_ok else '缺失'}"
            except json.JSONDecodeError as exc:
                detail = f"stdout 非合法 JSON: {exc}"
        else:
            detail += " | " + (proc.stderr or "").strip().splitlines()[-1][:120] \
                if proc.stderr.strip() else detail
        add("C14", "CLI 可运行且 --json 输出合法", 1, ok, detail)
    except Exception as exc:
        add("C14", "CLI 可运行且 --json 输出合法", 1, False, f"{exc!r}")

    # C15 零第三方依赖
    try:
        std = set(getattr(sys, "stdlib_module_names", set()))
        local = {p.stem for p in (sub_dir / "minichunk").rglob("*.py")}
        local |= {"minichunk"}
        foreign = set()
        for py in (sub_dir / "minichunk").rglob("*.py"):
            tree = ast.parse(py.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        foreign.add(a.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    foreign.add(node.module.split(".")[0])
        foreign -= std | local | {"__future__"}
        add("C15", "零第三方依赖", 1, not foreign,
            "OK" if not foreign else f"引入了: {sorted(foreign)}")
    except Exception as exc:
        add("C15", "零第三方依赖", 1, False, f"{exc!r}")

    rep.checks = [asdict(c) for c in checks]
    rep.score = sum(c.weight for c in checks if c.passed)
    rep.max_score = sum(c.weight for c in checks)
    rep.percent = round(rep.score / rep.max_score * 100, 1) if rep.max_score else 0.0
    return rep


# ---------------------------------------------------------------- 主流程

def main() -> int:
    ap = argparse.ArgumentParser(description="minichunk 提交物自动验收")
    ap.add_argument("submission", help="提交目录 (其下有 minichunk 包)")
    ap.add_argument("--label", default="", help="模型名, 用于报告标注")
    ap.add_argument("--out", default="verify_result.json", help="结果 JSON 输出路径")
    args = ap.parse_args()

    sub = Path(args.submission).resolve()
    if not (sub / "minichunk").is_dir():
        print(f"[FAIL] {sub} 下没有 minichunk 包目录")
        return 2

    label = args.label or sub.name
    rep = run_checks(sub, label)

    print("=" * 72)
    print(f"提交: {rep.submission}")
    print(f"标签: {rep.label}")
    print("=" * 72)
    for c in rep.checks:
        mark = "PASS" if c["passed"] else "FAIL"
        print(f"[{mark}] {c['cid']} (权重{c['weight']}) {c['name']}")
        if c["detail"]:
            print(f"        {c['detail']}")
    print("-" * 72)
    print(f"契约得分: {rep.score} / {rep.max_score}   ({rep.percent}%)")
    print("=" * 72)

    Path(args.out).write_text(
        json.dumps(asdict(rep), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"明细已写入 {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
