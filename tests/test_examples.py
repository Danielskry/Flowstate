import sys
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
if str(EXAMPLES) not in sys.path:
    sys.path.insert(0, str(EXAMPLES))

import github_review_grounding
import analytics_dashboard_grounding


def test_github_review_example_builds_expected_context() -> None:
    ctx = github_review_grounding.build_context()

    assert ctx.facts["surface"] == "pull_request"
    assert ctx.facts["repo"] == "acme/payments-service"
    assert ctx.facts["ci_status"] == "failed"
    assert ctx.intent["task"] == "understand why test_duplicate_charge_returns_202 is failing"
    assert ctx.steps[-1] == "read test log for test_idempotency.py"


def test_github_review_example_builds_message_list() -> None:
    messages = github_review_grounding.make_messages("Why is this test failing?")

    assert messages[0]["role"] == "system"
    assert "pull_request" in messages[0]["content"]
    assert messages[1] == {
        "role": "user",
        "content": "Why is this test failing?",
    }


def test_analytics_dashboard_example_builds_expected_context() -> None:
    ctx = analytics_dashboard_grounding.build_context()

    assert ctx.facts["surface"] == "analytics_dashboard"
    assert ctx.facts["active_metric"] == "checkout_conversion_rate"
    assert ctx.facts["funnel_drop_off_step"] == "payment_details"
    assert ctx.intent["stage"] == "root cause analysis"
    assert ctx.steps[0] == "opened overview dashboard"
