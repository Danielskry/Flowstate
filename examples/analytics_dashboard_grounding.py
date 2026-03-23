"""
SaaS analytics dashboard assistant — grounding example.

Shows how context builds as a user drills into a metrics dashboard,
so that when they open the chat the assistant already understands
which metric they are investigating and what anomaly they spotted.
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
        scope={"user_id": "analyst-7", "org_id": "org-acme"},
        max_steps=5,
    )

    # User opens the dashboard
    ctx.set_fact("surface", "analytics_dashboard")
    ctx.set_fact("product", "GrowthLens")
    ctx.add_step("opened overview dashboard")

    # User notices a drop in conversion rate
    ctx.set_fact("active_metric", "checkout_conversion_rate")
    ctx.set_fact("metric_value_current", "2.1%")
    ctx.set_fact("metric_value_prior_week", "3.8%")
    ctx.add_step("selected metric: checkout_conversion_rate")
    ctx.set_intent("task", "investigate conversion rate drop")

    # User filters to a specific segment
    ctx.set_fact("active_segment", "mobile / US / new users")
    ctx.add_step("applied segment filter: mobile, US, new users")
    ctx.set_intent("stage", "root cause analysis")

    # User opens the funnel view
    ctx.set_fact("funnel_drop_off_step", "payment_details")
    ctx.set_fact("funnel_drop_off_rate", "61%")
    ctx.add_step("opened checkout funnel breakdown")
    ctx.set_intent("task", "understand why new mobile users abandon at payment_details")

    return ctx


def make_messages(user_message: str) -> list[dict[str, str]]:
    return [build_context().as_message(), {"role": "user", "content": user_message}]


def simulate() -> None:
    ctx = build_context()

    print("Context when the analyst opens the chat")
    print("========================================")
    print(ctx.render())
    print()

    user_question = "What could explain this drop and what should I look at next?"
    messages = make_messages(user_question)

    print("Messages sent to the agent")
    print("==========================")
    for msg in messages:
        print(f"[{msg['role']}]")
        print(msg["content"])
        print()


if __name__ == "__main__":
    simulate()
