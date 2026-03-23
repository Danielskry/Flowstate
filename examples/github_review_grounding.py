"""
GitHub PR review assistant — grounding example.

Shows how context accumulates as a developer reviews a pull request,
so that when they open the assistant the agent already knows what they
are looking at and what the CI failure is about.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from flowstate import Context
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from flowstate import Context


def build_context() -> Context:
    ctx = Context(
        scope={"user_id": "eng-99", "session_id": "sess-pr-review"},
        max_steps=6,
    )

    # Developer opens the PR
    ctx.set_fact("surface", "pull_request")
    ctx.set_fact("repo", "acme/payments-service")
    ctx.set_fact("pr_number", 847)
    ctx.set_fact("pr_title", "Add idempotency key support to charge endpoint")
    ctx.add_step("opened PR #847")

    # Browsing changed files
    ctx.set_fact("current_file", "src/charges/views.py")
    ctx.add_step("viewed diff: src/charges/views.py (+112 / -34)")
    ctx.set_intent("task", "reviewing charge endpoint changes")

    # CI is red
    ctx.set_fact("ci_status", "failed")
    ctx.set_fact("failed_check", "test / unit-tests")
    ctx.add_step("clicked failing CI check: test / unit-tests")

    # Developer reads the test log
    ctx.set_fact(
        "test_failure",
        "FAILED tests/charges/test_idempotency.py::test_duplicate_charge_returns_202"
        " — AssertionError: assert 400 == 202",
    )
    ctx.add_step("read test log for test_idempotency.py")
    ctx.set_intent("task", "understand why test_duplicate_charge_returns_202 is failing")

    return ctx


def make_messages(user_message: str) -> list[dict[str, str]]:
    return [build_context().as_message(), {"role": "user", "content": user_message}]


def simulate() -> None:
    ctx = build_context()

    print("Context when the developer asks for help")
    print("=========================================")
    print(ctx.render())
    print()

    user_question = "Why is this test failing and how do I fix it?"
    messages = make_messages(user_question)

    print("Messages sent to the agent")
    print("==========================")
    for msg in messages:
        print(f"[{msg['role']}]")
        print(msg["content"])
        print()


if __name__ == "__main__":
    simulate()
