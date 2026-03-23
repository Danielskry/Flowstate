# Flowstate

Flowstate is a small Python library for maintaining behavioral context for AI agents.

Instead of retrieval context from documents or knowledge context from static reference data, Flowstate keeps the user's live workflow state structured and current. Your agent reads it as background context before responding.

![flowstate flowchart](https://raw.githubusercontent.com/Danielskry/Latent-Workflow-Grounding/main/assets/diagram.drawio.svg)

## Install

```bash
pip install flowstate-ai
```

## Quick start

Create one context per session and update it as the user moves through your product:

```python
from flowstate import Context

ctx = Context(scope={"user_id": "traveller-301"}, max_steps=4)

# traveller opens their booking and sees a delay
ctx.set_fact("flight", "BA 442 — London Heathrow to Amsterdam")
ctx.set_fact("scheduled_departure", "16:45")
ctx.set_fact("status", "Delayed — 2 hours (new departure: 18:45)")
ctx.set_fact("gate", "B22, closes 18:15")
ctx.add_step("opened booking")
ctx.add_step("saw delay notification")
ctx.add_step("tapped 'Is my flight on time?'")
ctx.set_intent("task", "decide whether to leave for the airport now")

# traveller asks a question — agent already knows the full picture
messages = [ctx.as_message(), {"role": "user", "content": user_input}]
```

`ctx.as_message()` renders to:

```
Scope:
  user id: traveller-301

Facts:
  flight: BA 442 — London Heathrow to Amsterdam
  scheduled departure: 16:45
  status: Delayed — 2 hours (new departure: 18:45)
  gate: B22, closes 18:15

Steps:
  opened booking
  saw delay notification
  tapped 'Is my flight on time?'

Intent:
  task: decide whether to leave for the airport now
```

## Demo

A traveller's flight is delayed. They open the app and type:

> **"Do I need to leave now?"**

Your app has been watching. It knows which flight they're on, the new departure time, and when the gate closes. That gets passed to the assistant as background:

```
Facts:
  flight: BA 442 — London Heathrow to Amsterdam
  scheduled departure: 16:45
  status: Delayed — 2 hours (new departure: 18:45)
  gate: B22, closes 18:15

Steps:
  opened booking
  saw delay notification
  tapped 'Is my flight on time?'

Intent:
  task: decide whether to leave for the airport now
```

| Assistant with background | Assistant without |
|---|---|
| No rush — your flight has been pushed to 18:45 and gate B22 closes at 18:15. As long as you can reach Heathrow by 17:45 you're fine. You have about 2 extra hours compared to your original plan. | Which flight are you on, and what time does it depart? |

Without background the assistant can't answer at all.

```bash
python examples/evaluation.py
# → examples/evaluation_report.html
```

## The model

`Context` has four sections:

| Section | Type | Holds |
|---|---|---|
| `scope` | `dict` | Tenant, user, and session identifiers |
| `facts` | `dict` | Durable known state |
| `steps` | `list[str]` | Observed user progression |
| `intent` | `dict` | Current inferred goal |

## Updating context

Use individual setters for explicit writes:

```python
ctx.set_fact("current_page", "settings reference")
ctx.add_step("opened settings reference")
ctx.set_intent("task", "understand a configuration error")
```

Use merge helpers when multiple app surfaces contribute to the same section:

```python
ctx.merge_facts({
    "docs": {"current_page": "settings reference"},
    "errors": {"current_error": "ImproperlyConfigured"},
})
```

Use `merge()` to combine two independently built contexts:

```python
ctx.merge(other_ctx)
```

## Exports

```python
ctx.render()      # plain text for prompts
ctx.as_message()  # {"role": "system", "content": ...} for chat APIs
ctx.to_dict()     # plain Python dict
ctx.to_schema()   # validated Pydantic model
```

## Validation

Optional. Subclass `ContextSchema` to add Pydantic checks:

```python
from flowstate import ContextSchema

class DocsContextSchema(ContextSchema):
    facts: dict[str, str]

validated = ctx.validate(DocsContextSchema)
```
