#!/usr/bin/env python3
"""Policy simulation: replay the recorded failure trajectory through each SAC variant.

This is deterministic and uses no model calls. It answers the question the LLM
matrix can only answer statistically:

    Given exactly the actions the failing session took, what does each policy
    variant keep in context, flag, or refuse?

The scripted agent behaves like the recorded one: it ends by registering
`seal_count = 5` from the detector threshold and calling finish.

Usage:
    python3 harness/policy_sim.py work/sessions/single_action.jsonl
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sac.agent import DERIVED_IMAGE, RunLedger  # noqa: E402

VARIANTS = ("v9", "v10", "v11", "v12", "v13")
PIN_IMAGES = 6


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def actions_of(rows: list[dict]) -> list[dict]:
    """Ordered tool calls with their observations (text) and image paths."""
    calls: dict[str, dict] = {}
    order: list[dict] = []
    for event in rows:
        if event["type"] == "tool/call":
            name = event["data"].get("name", "")
            try:
                args = json.loads(event["data"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            entry = {"step": event["data"].get("step", 0), "tool": name, "args": args,
                     "text": "", "images": []}
            calls[event["data"].get("callId")] = entry
            order.append(entry)
    for event in rows:
        if event["type"] != "tool/result":
            continue
        entry = calls.get(event["data"]["message"].get("toolCallId"))
        if entry is None:
            continue
        blocks = event["data"]["message"].get("content") or []
        entry["text"] = " ".join(block.get("text", "") for block in blocks
                                 if isinstance(block, dict) and block.get("type") == "text")
        entry["images"] = [block for block in blocks
                           if isinstance(block, dict) and block.get("type") in ("image", "image_url")]
    return order


def image_path(entry: dict) -> str:
    for key in ("file_path", "path", "input"):
        if key in entry["args"]:
            return str(entry["args"][key])
    return ""


def simulate(actions: list[dict], variant: str) -> dict:
    ledger = RunLedger(images=True, repeats=True)
    repeats: list[int] = []
    for entry in actions:
        seen = ledger.already_seen(entry["tool"], entry["args"])
        if seen is not None:
            repeats.append(entry["step"])
            ledger.repeat_steps.append(entry["step"])
        ledger.observe(entry["tool"], entry["args"], entry["text"], entry["step"])

    images = [(image_path(entry), entry["step"]) for entry in actions if entry["images"]]
    raw = [(path, step) for path, step in images if not DERIVED_IMAGE.search(Path(path).name)]
    final_step = actions[-1]["step"] if actions else 0

    pinned = set()
    if variant != "v9":
        pinned = {path for path, _ in images[-PIN_IMAGES:]}

    verdict = {"variant": variant, "images_in_context": len(pinned) if variant != "v9" else 0,
               "repeats_flagged": len(repeats), "gate": "pass", "reason": ""}

    # Scripted conclusion: register the detector count and finish.
    ledger_note = {"subject": "seal_count", "value": "5",
                   "evidence": "hough: 5 circles above 0.72*best, 18 weak responses dismissed as noise",
                   "method": "script"}
    notes = [ledger_note]

    if variant in ("v11", "v12", "v13"):
        if not notes or any(not note["evidence"] for note in notes):
            verdict.update(gate="block", reason="claim without evidence")
        elif variant in ("v12", "v13"):
            conflicts = group_conflicts(notes)
            if conflicts:
                verdict.update(gate="block", reason="contradictory claims")
            elif variant == "v13" and script_only(notes, "seal_count"):
                verdict.update(gate="block",
                               reason="seal_count=5 comes only from a script threshold; an independent "
                                      "observation is required")
            elif variant == "v13" and raw and final_step - raw[-1][1] > 3:
                verdict.update(gate="block",
                               reason=f"last raw image observation is {final_step - raw[-1][1]} steps old")
    verdict["last_raw_image_age"] = final_step - raw[-1][1] if raw else None
    verdict["notes"] = notes
    return verdict


def group_conflicts(notes: list[dict]) -> list[str]:
    groups: dict[str, list[dict]] = {}
    for note in notes:
        groups.setdefault(note["subject"], []).append(note)
    out = []
    for subject, items in groups.items():
        if len({item["value"] for item in items}) > 1:
            out.append(subject)
    return out


def script_only(notes: list[dict], subject: str) -> bool:
    items = [note for note in notes if note["subject"] == subject]
    methods = {note["method"] for note in items}
    return len(methods) == 1 and any(key in next(iter(methods)) for key in ("script", "hough", "detect"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("session", help="decompressed session.v4.jsonl")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    actions = actions_of(load(Path(args.session)))
    rows = [simulate(actions, variant) for variant in VARIANTS]
    lines = [
        "| 变体 | 结论时仍可见的原始图像 | 账本标出的重复动作 | finish 门控 | 触发原因 |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['variant']} | {row['images_in_context']} 张 | {row['repeats_flagged']} 次 | "
            f"{'放行' if row['gate'] == 'pass' else '拦截'} | {row['reason'] or '—'} |"
        )
    text = "\n".join(lines) + "\n"
    print(text)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())