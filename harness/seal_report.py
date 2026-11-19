#!/usr/bin/env python3
"""Seal-task report: one row per run with the evidence that explains the score."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sac.tasks import _SEAL_NAMES, _parse_seal_count  # noqa: E402


def load(paths):
    rows = []
    for path in paths:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", nargs="+")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    rows = [row for row in load(args.results) if row.get("task_id") == "seal_count"]
    rows.sort(key=lambda row: (row.get("regime", ""), row.get("state_version") or "", row.get("repeat", 0)))

    lines = [
        "| 范式 / 版本 | 重复 | 分数 | 判定 | 声称数量 | 识别名称 | 步数 | 看图 | 重复动作 | 压缩 | 峰值上下文 | 墙钟 s |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        answer = row.get("answer") or ""
        count = _parse_seal_count(answer)
        hits = sum(1 for name, aliases in _SEAL_NAMES if any(alias in answer for alias in aliases))
        ledger = row.get("ledger") or {}
        trace = row.get("trace") or []
        views = sum(1 for item in trace
                    if isinstance(item, dict) and "view_image" in (item.get("tool_calls") or []))
        label = row.get("regime", "?") + (f"-{row['state_version']}" if row.get("state_version") else "")
        lines.append(
            f"| {label} | {row.get('repeat', 0) + 1} | {row.get('score', 0):.2f} | "
            f"{'✅' if row.get('ok') else '❌'} | {count if count is not None else '-'} | {hits}/5 | "
            f"{row.get('actions', 0)} | {views} | {ledger.get('repeats', 0)} | "
            f"{row.get('compactions', 0)} | {row.get('peak_prompt_tokens', 0):,} | {row.get('wall_s', 0):.0f} |"
        )
    text = "\n".join(lines) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())