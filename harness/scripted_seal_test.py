#!/usr/bin/env python3
"""End-to-end scripted-agent test for the seal task (no external model calls).

The scripted client replays the failing trajectory (look at the page, look at
the rows, run the detector, answer "5") and reacts to the harness exactly like a
cooperative model would: when `finish` is refused with a gate message, it
re-observes the image and answers again.

This validates the loop mechanics that the LLM matrix cannot validate while the
provider endpoint is unstable:

    v9  : finish is accepted with 5      -> wrong answer
    v13 : finish is refused, model re-views, then answers 6

Usage:
    python3 harness/scripted_seal_test.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sac.agent import Runner  # noqa: E402
from sac.llm import Completion, Usage  # noqa: E402
from sac.tasks import TASKS  # noqa: E402
from sac.tokens import TokenMeter  # noqa: E402

WORKSPACE = Path("runs/scripted_seal")

SEQUENCE = [
    ("bash", {"command": "ls -la"}),
    ("view_image", {"path": "page.jpg"}),
    ("view_image", {"path": "row_01.jpg"}),
    ("view_image", {"path": "row_02.jpg"}),
    ("view_image", {"path": "row_03.jpg"}),
    ("view_image", {"path": "row_04.jpg"}),
    ("view_image", {"path": "row_05.jpg"}),
    ("bash", {"command": "$SAC_PYTHON seals.py --min-score 0.72"}),
]

ANSWER_FIVE = (
    "结论：共 5 枚印章，分别对应五个审批栏，每栏 1 枚。"
    "依据：圆检测恰好有 5 个强响应圆，其余弱响应属于签名误检。"
)
ANSWER_SIX = (
    "结论：共 6 枚印章。逐枚为：湖南经研电力设计有限公司（承建单位）、"
    "国网湖南省电力有限公司经济技术研究院（建设单位）、数字智能研究中心（专业管理部门）、"
    "发展策划部（专业管理部门）、国网湖南省电力有限公司经济技术研究院（运维单位）、"
    "科技数字化部（数字化职能管理部门）。"
)


class ScriptedClient:
    """Deterministic client: a fixed action queue plus gate-aware retry."""

    def __init__(self) -> None:
        self.index = 0
        self.reviewed = False

    @staticmethod
    def _last_tool_text(messages: list[dict]) -> str:
        for message in reversed(messages):
            if message.get("role") == "tool":
                content = message.get("content")
                return content if isinstance(content, str) else ""
        return ""

    def complete(self, *, model, messages, tools=None, max_tokens=8192,
                 temperature=0.2, tool_choice=None, purpose="action") -> Completion:
        usage = Usage(prompt_tokens=1400, completion_tokens=80)
        last = self._last_tool_text(messages)

        if last.startswith("[gate]"):
            if "register at least one claim" in last:
                return self._calls([("note", {"subject": "seal_count", "value": "5",
                                              "evidence": "seals.py: 5 circles above 0.72*best",
                                              "method": "script"})], usage)
            # Independent observation required: look again, record what is seen, answer.
            return self._calls([
                ("view_image", {"path": "row_03.jpg"}),
                ("note", {"subject": "seal_count", "value": "6",
                          "evidence": "row_03/row_05 re-view: two stars in the professional row, one in operations",
                          "method": "visual"}),
                ("finish", {"answer": ANSWER_SIX}),
            ], usage)

        if self.index < len(SEQUENCE):
            name, arguments = SEQUENCE[self.index]
            self.index += 1
            return self._calls([(name, arguments)], usage)
        return self._calls([("finish", {"answer": ANSWER_FIVE})], usage)

    def complete_text(self, *, model, messages, max_tokens=8192,
                      temperature=0.2, purpose="text") -> Completion:
        usage = Usage(prompt_tokens=900, completion_tokens=120)
        return Completion(
            content=("OBJECTIVE: count the seals and identify them.\n"
                     "FACTS:\n- detector reported 5 circles above 0.72*best\n"
                     "IMAGES_OBSERVED:\n- page.jpg: red seals clustered in the approval rows\n"
                     "NEXT: finish with the count."),
            reasoning="", tool_calls=[], usage=usage, latency_s=0.0, finish_reason="stop")

    @staticmethod
    def _calls(items: list[tuple[str, dict]], usage: Usage) -> Completion:
        calls = []
        for name, arguments in items:
            calls.append({"id": f"call_{name}_{len(calls)}_{abs(hash(json.dumps(arguments, sort_keys=True))) % 10**6}",
                          "name": name,
                          "arguments": json.dumps(arguments, ensure_ascii=False)})
        return Completion(content="", reasoning="", tool_calls=calls, usage=usage,
                          latency_s=0.0, finish_reason="tool_calls")


def run_variant(version: str) -> dict:
    task = TASKS["seal_count"]
    workdir = Path(f"{WORKSPACE}_{version}")
    scoped = type(task)(id=task.id, prompt=task.prompt, input_details=task.input_details,
                        workdir=workdir, setup=task.setup, verify=task.verify,
                        category=task.category, max_actions=task.max_actions)
    runner = Runner(ScriptedClient(), TokenMeter(), model="scripted",
                    regime="sac", state_version=version, max_actions=18)
    result = runner.run(scoped)
    return {"version": version, "ok": result.ok, "score": result.score,
            "detail": result.detail, "gated": result.gated_steps,
            "answer": result.answer[:120]}


def main() -> int:
    rows = [run_variant(version) for version in ("v9", "v13")]
    print("| 变体 | 分数 | 通过 | 门控拦截次数 | 最终答案（截断） |")
    print("|---|---|---|---|---|")
    for row in rows:
        print(f"| {row['version']} | {row['score']:.2f} | {'✅' if row['ok'] else '❌'} | "
              f"{row['gated']} | {row['answer']} |")
    expected = {"v9": False, "v13": True}
    failures = [row for row in rows if row["ok"] != expected[row["version"]]]
    if failures:
        print(f"\nUNEXPECTED: {[(row['version'], row['ok'], row['detail']) for row in failures]}")
        return 1
    print("\nscripted test passed: v9 accepts the wrong count, v13 forces a re-observation and passes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())