"""
flowstate — demo.

Runs the delayed flight scenario with and without flowstate context and writes
a self-contained HTML showing the two responses side by side.

Usage
-----
    python examples/evaluation.py

Output
------
    examples/evaluation_report.html
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from html import escape
from pathlib import Path

import anthropic

# ---------------------------------------------------------------------------
# Bootstrap: load .env, add src/ to path
# ---------------------------------------------------------------------------

def _load_env() -> None:
    for candidate in [Path(".env"), Path("../.env"), Path(__file__).parent.parent / ".env"]:
        if candidate.exists():
            for raw in candidate.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())
            return


_load_env()
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from flowstate import Context  # noqa: E402

client = anthropic.Anthropic(api_key=os.environ["CLAUDE_KEY"])

MODEL = "claude-haiku-4-5-20251001"

REPORT_PATH = Path(__file__).parent / "evaluation_report.html"

# ---------------------------------------------------------------------------
# Scenario
# ---------------------------------------------------------------------------

QUESTION = "Do I need to leave now?"

GENERIC_SYSTEM = "You are a helpful travel assistant. Answer the user's question concisely."


def build_context() -> Context:
    ctx = Context(scope={"user_id": "traveller-301"}, max_steps=4)
    ctx.set_fact("flight", "BA 442 — London Heathrow to Amsterdam")
    ctx.set_fact("scheduled_departure", "16:45")
    ctx.set_fact("status", "Delayed — 2 hours (new departure: 18:45)")
    ctx.set_fact("gate", "B22, closes 18:15")
    ctx.add_step("opened booking")
    ctx.add_step("saw delay notification")
    ctx.add_step("tapped 'Is my flight on time?'")
    ctx.set_intent("task", "decide whether to leave for the airport now")
    return ctx


def ask(messages: list[dict]) -> str:
    system_text = None
    user_messages = []
    for msg in messages:
        if msg["role"] == "system":
            system_text = msg["content"]
        else:
            user_messages.append(msg)

    kwargs: dict = dict(model=MODEL, max_tokens=400, messages=user_messages)
    if system_text:
        kwargs["system"] = system_text
    return client.messages.create(**kwargs).content[0].text.strip()


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
       font-size: 15px; line-height: 1.6; color: #1a1a1a; background: #f5f5f5; }
.page { max-width: 960px; margin: 0 auto; padding: 48px 24px; }
h1 { font-size: 1.6rem; font-weight: 700; margin-bottom: 6px; }
.meta { font-size: 0.85rem; color: #999; margin-bottom: 40px; }

.question { background: #f0f4ff; border-left: 3px solid #4a6cf7; padding: 10px 14px;
            border-radius: 0 6px 6px 0; margin-bottom: 24px;
            font-size: 1.1rem; font-style: italic; }

.context-block { background: #1e1e1e; color: #d4d4d4; font-family: monospace;
                 font-size: 0.82rem; line-height: 1.5; padding: 14px 16px;
                 border-radius: 6px; margin-bottom: 8px; white-space: pre-wrap; }
.context-toggle { font-size: 0.82rem; color: #4a6cf7; cursor: pointer;
                  margin-bottom: 24px; display: inline-block; }

.split { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.response-box { border-radius: 8px; padding: 20px; }
.response-box.grounded   { background: #f0fdf4; border: 1px solid #86efac; }
.response-box.ungrounded { background: #fff5f5; border: 1px solid #fca5a5; }
.response-label { font-size: 0.78rem; font-weight: 700; text-transform: uppercase;
                  letter-spacing: .05em; margin-bottom: 10px; }
.grounded   .response-label { color: #16a34a; }
.ungrounded .response-label { color: #dc2626; }
.response-text { font-size: 0.92rem; line-height: 1.6; }
.response-text p  { margin-bottom: 10px; }
.response-text p:last-child { margin-bottom: 0; }
.response-text h1, .response-text h2, .response-text h3 {
  font-size: 0.95rem; font-weight: 700; margin: 14px 0 4px; }
.response-text h1:first-child, .response-text h2:first-child, .response-text h3:first-child {
  margin-top: 0; }
.response-text ul, .response-text ol { padding-left: 20px; margin-bottom: 10px; }
.response-text li { margin-bottom: 4px; }
.response-text pre { background: rgba(0,0,0,0.06); border-radius: 5px;
  padding: 10px 12px; margin: 10px 0; overflow-x: auto; }
.response-text pre code { background: none; padding: 0; font-size: 0.8rem; }
.response-text code { background: rgba(0,0,0,0.07); border-radius: 3px;
  padding: 1px 5px; font-size: 0.82rem; font-family: monospace; }
"""

SCRIPTS = """
function toggle(id) {
  const el = document.getElementById(id);
  const btn = document.getElementById('btn-' + id);
  if (el.style.display === 'none') {
    el.style.display = 'block'; btn.textContent = 'Hide context';
  } else {
    el.style.display = 'none'; btn.textContent = 'Show context';
  }
}
"""


def build_report(context_text: str, grounded: str, ungrounded: str) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>flowstate Demo</title>
<script src="https://cdn.jsdelivr.net/npm/marked@9/marked.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<div class="page">

  <h1>flowstate &mdash; Demo</h1>
  <div class="meta">
    Model: {escape(MODEL)} &nbsp;|&nbsp; Generated: {generated_at}
  </div>

  <div class="question">"{escape(QUESTION)}"</div>

  <span class="context-toggle" id="btn-ctx" onclick="toggle('ctx')">Show context</span>
  <div class="context-block" id="ctx" style="display:none">{escape(context_text)}</div>

  <div class="split">
    <div class="response-box grounded">
      <div class="response-label">&#x2714; With flowstate context</div>
      <div class="response-text" id="resp-grounded"></div>
    </div>
    <div class="response-box ungrounded">
      <div class="response-label">&#x2718; Without context</div>
      <div class="response-text" id="resp-ungrounded"></div>
    </div>
  </div>

</div>
<script>
{SCRIPTS}
const GROUNDED   = {json.dumps(grounded)};
const UNGROUNDED = {json.dumps(ungrounded)};
document.getElementById('resp-grounded').innerHTML   = marked.parse(GROUNDED);
document.getElementById('resp-ungrounded').innerHTML = marked.parse(UNGROUNDED);
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Model : {MODEL}")
    print(f"Question : {QUESTION!r}")
    print()

    ctx = build_context()

    print("  grounded call...")
    grounded = ask([ctx.as_message(), {"role": "user", "content": QUESTION}])
    time.sleep(2)

    print("  ungrounded call...")
    ungrounded = ask([
        {"role": "system", "content": GENERIC_SYSTEM},
        {"role": "user", "content": QUESTION},
    ])

    print()
    print("Writing report...")
    REPORT_PATH.write_text(build_report(ctx.render(), grounded, ungrounded), encoding="utf-8")
    print(f"Done -> {REPORT_PATH}")
