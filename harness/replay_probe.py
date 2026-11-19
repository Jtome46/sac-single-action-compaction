#!/usr/bin/env python3
"""Replay the real SAC session through the v10+ policies and measure what survives.

This is a deterministic probe (no model calls): it reconstructs the session
surface step by step from the recorded events and answers three questions that
the LLM matrix can only answer statistically:

  1. How many of the image observations are still in context at the final step
     under (a) plain SAC, (b) SAC with image pinning?
  2. How many repeated actions would the ledger flag?
  3. What does the machine ledger say about the evidence at the moment the model
     concluded "5 seals"?

Usage:
    python3 harness/replay_probe.py work/sessions/single_action.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sac.agent import RunLedger  # noqa: E402


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def surface_after(rows: list[dict], compactions: int) -> set[int]:
    """Surface sequence numbers after the first `compactions` compactions."""
    shadowed: set[int] = set()
    seen = 0
    for event in rows:
        if event["type"] != "compaction/summary":
            continue
        if seen >= compactions:
            break
        seen += 1
        shadowed.update(event["data"].get("shadowedSeqs") or [])
    return {event["seq"] for event in rows if event.get("seq") is not None and event["seq"] not in shadowed}


def is_image_result(event: dict) -> bool:
    blocks = event.get("data", {}).get("message", {}).get("content")
    if not isinstance(blocks, list):
        return False
    return any(isinstance(block, dict) and block.get("type") == "image" for block in blocks)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("session", help="decompressed session.v4.jsonl")
    parser.add_argument("--pin", type=int, default=6)
    args = parser.parse_args()

    rows = load(Path(args.session))
    for index, event in enumerate(rows):
        event["_index"] = index
    compactions = [event for event in rows if event["type"] == "compaction/summary"]
    images = [event for event in rows if event["type"] == "tool/result" and is_image_result(event)]
    print(f"events={len(rows)} compactions={len(compactions)} image_results={len(images)}")

    # --- 1. image survival at the final step ---------------------------------
    final_surface = surface_after(rows, len(compactions))
    survived = [event for event in images if event["seq"] in final_surface]
    print(f"final surface: {len(final_surface)} seqs")
    print(f"image results still in context, plain SAC: {len(survived)}/{len(images)}")

    # v10 rule: the newest `pin` image results are never folded. The span end is
    # pulled back before the pin-th newest image, so everything from there on stays.
    if images:
        pinned = images[-args.pin:]
        first_pinned_seq = min(event["seq"] for event in pinned)
        pinned_kept = [event for event in images if event["seq"] >= first_pinned_seq]
        print(f"image results kept with pinImages={args.pin}: {len(pinned_kept)}/{len(images)} "
              f"(seqs >= {first_pinned_seq})")

    # --- 2. repeated actions the ledger would flag ---------------------------
    calls: dict[str, tuple[int, str]] = {}
    ledger = RunLedger(images=True, repeats=True)
    for event in rows:
        if event["type"] != "tool/call":
            continue
        name = event["data"].get("name", "")
        try:
            arguments = json.loads(event["data"].get("arguments") or "{}")
        except json.JSONDecodeError:
            arguments = {}
        key = ledger.call_key(name, arguments)
        if key in calls:
            ledger.repeat_steps.append(event["data"].get("step", 0))
        else:
            calls[key] = (event["data"].get("step", 0), "")
        ledger.observe(name, arguments, "", event["data"].get("step", 0))
    print(f"distinct actions={len(calls)} repeated_calls={len(ledger.repeat_steps)} "
          f"at steps {sorted(set(ledger.repeat_steps))}")

    # --- 3. what the ledger knows about the seal evidence --------------------
    seen_commands = []
    for event in rows:
        if event["type"] != "tool/call":
            continue
        name = event["data"].get("name", "")
        try:
            arguments = json.loads(event["data"].get("arguments") or "{}")
        except json.JSONDecodeError:
            continue
        if name == "bash":
            command = " ".join(str(arguments.get("command", "")).split())
            if "hough" in command or "seals" in command:
                seen_commands.append(command[:120])
        if name == "read_image":
            seen_commands.append(f"read_image {arguments.get('file_path', '')}")
    print("evidence-bearing actions recorded by the ledger:")
    for command in seen_commands:
        print(f"  - {command}")

    print("\ninterpretation:")
    print(f"  * plain SAC keeps {len(survived)} image observation(s) at answer time; "
          f"pinImages={args.pin} keeps {len(images) if not images else len(pinned_kept)}.")
    print(f"  * the ledger exposes {len(ledger.repeat_steps)} re-run(s) that plain SAC hides.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())