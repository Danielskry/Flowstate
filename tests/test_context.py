import pytest

from flowstate import Context, ContextSchema


class StringOnlyContextSchema(ContextSchema):
    facts: dict[str, str]
    intent: dict[str, str]


def test_init_kwargs_populate_state() -> None:
    ctx = Context(
        facts={"product": "Django"},
        steps=["opened documentation"],
        intent={"task": "understand an error"},
    )

    assert ctx.facts == {"product": "Django"}
    assert ctx.steps == ["opened documentation"]
    assert ctx.intent == {"task": "understand an error"}


def test_init_kwargs_are_copied() -> None:
    source_facts = {"product": "Django", "docs": {"current_page": "settings reference"}}
    source_steps = ["opened documentation"]
    source_intent = {"task": {"name": "debug"}}
    source_scope = {"session": {"id": "sess-123"}}

    ctx = Context(
        facts=source_facts,
        steps=source_steps,
        intent=source_intent,
        scope=source_scope,
    )

    source_facts["product"] = "Flask"
    source_facts["docs"]["current_page"] = "forms reference"
    source_steps.append("opened forms guide")
    source_intent["task"]["name"] = "rewrite a view"
    source_scope["session"]["id"] = "sess-456"

    assert ctx.facts == {
        "product": "Django",
        "docs": {"current_page": "settings reference"},
    }
    assert ctx.steps == ["opened documentation"]
    assert ctx.intent == {"task": {"name": "debug"}}
    assert ctx.scope == {"session": {"id": "sess-123"}}


def test_set_and_update_facts() -> None:
    ctx = Context()

    ctx.set_fact("product", "Django").update_facts(
        {"surface": "documentation"},
        current_page="QuerySet API",
    )

    assert ctx.facts == {
        "product": "Django",
        "surface": "documentation",
        "current_page": "QuerySet API",
    }


def test_remove_fact_returns_previous_value() -> None:
    ctx = Context(facts={"current_page": "errors reference"})

    removed = ctx.remove_fact("current_page")

    assert removed == "errors reference"
    assert ctx.facts == {}


def test_add_extend_and_pop_steps() -> None:
    ctx = Context()

    ctx.add_step(" opened docs ").extend_steps(
        ["opened model reference", "opened field options"]
    )

    popped = ctx.pop_step()

    assert popped == "opened field options"
    assert ctx.steps == ["opened docs", "opened model reference"]


def test_set_and_update_intent() -> None:
    ctx = Context()

    ctx.set_intent("task", "understand a validation error").update_intent(
        {"mode": "self-serve"},
        urgency="high",
    )

    assert ctx.intent == {
        "task": "understand a validation error",
        "mode": "self-serve",
        "urgency": "high",
    }


def test_remove_intent_returns_previous_value() -> None:
    ctx = Context(intent={"task": "compare products"})

    removed = ctx.remove_intent("task")

    assert removed == "compare products"
    assert ctx.intent == {}


def test_clear_resets_all_sections() -> None:
    ctx = Context(
        facts={"product": "Django"},
        steps=["opened documentation"],
        intent={"task": "debug"},
        scope={"session_id": "sess-123"},
    )

    ctx.clear()

    assert ctx.facts == {}
    assert ctx.steps == []
    assert ctx.intent == {}
    assert ctx.scope == {}


def test_render_includes_all_sections() -> None:
    text = Context(
        facts={"product": "Django", "current_page": "settings reference"},
        steps=["opened documentation", "opened settings reference"],
        intent={"task": "understand a configuration error"},
    ).render()

    assert text == (
        "Facts:\n"
        "  product: Django\n"
        "  current page: settings reference\n\n"
        "Steps:\n"
        "  opened documentation\n"
        "  opened settings reference\n\n"
        "Intent:\n"
        "  task: understand a configuration error"
    )


def test_read_is_alias_for_render() -> None:
    ctx = Context(facts={"wishlist_items": 2})

    assert ctx.read() == ctx.render()


def test_render_is_empty_with_no_state() -> None:
    assert Context().render() == ""


def test_as_message_returns_plain_system_dict() -> None:
    ctx = Context(facts={"product": "Django"})

    assert ctx.as_message() == {
        "role": "system",
        "content": "Facts:\n  product: Django",
    }


def test_to_dict_returns_copies() -> None:
    ctx = Context(
        facts={"product": "Django", "docs": {"current_page": "settings reference"}},
        steps=["opened documentation"],
        intent={"task": {"name": "debug"}},
        scope={"session": {"id": "sess-123"}},
    )

    payload = ctx.to_dict()
    facts = payload["facts"]
    steps = payload["steps"]
    intent = payload["intent"]
    scope = payload["scope"]

    assert isinstance(facts, dict)
    assert isinstance(steps, list)
    assert isinstance(intent, dict)
    assert isinstance(scope, dict)

    facts["product"] = "Flask"
    facts["docs"]["current_page"] = "forms reference"
    steps.append("opened deployment guide")
    intent["task"]["name"] = "rewrite a view"
    scope["session"]["id"] = "sess-456"

    assert ctx.facts == {
        "product": "Django",
        "docs": {"current_page": "settings reference"},
    }
    assert ctx.steps == ["opened documentation"]
    assert ctx.intent == {"task": {"name": "debug"}}
    assert ctx.scope == {"session": {"id": "sess-123"}}


def test_from_dict_builds_context() -> None:
    ctx = Context.from_dict(
        {
            "facts": {"product": "Django"},
            "steps": ["opened documentation"],
            "intent": {"task": "debug"},
            "scope": {"session_id": "sess-123"},
        }
    )

    assert ctx.facts == {"product": "Django"}
    assert ctx.steps == ["opened documentation"]
    assert ctx.intent == {"task": "debug"}
    assert ctx.scope == {"session_id": "sess-123"}


def test_to_schema_and_from_schema_round_trip() -> None:
    original = Context(
        facts={"product": "Django"},
        steps=["opened documentation"],
        intent={"task": "debug"},
        scope={"session_id": "sess-123"},
    )

    schema = original.to_schema()
    restored = Context.from_schema(schema)

    assert restored.facts == {"product": "Django"}
    assert restored.steps == ["opened documentation"]
    assert restored.intent == {"task": "debug"}
    assert restored.scope == {"session_id": "sess-123"}


def test_validate_supports_custom_schema() -> None:
    ctx = Context(
        facts={"product": "Django"},
        intent={"task": "debug"},
    )

    validated = ctx.validate(StringOnlyContextSchema)

    assert validated.facts == {"product": "Django"}
    assert validated.intent == {"task": "debug"}


def test_pop_step_on_empty_context_raises() -> None:
    with pytest.raises(IndexError):
        Context().pop_step()


def test_blank_step_is_rejected() -> None:
    with pytest.raises(ValueError):
        Context().add_step("   ")


def test_blank_key_is_rejected() -> None:
    with pytest.raises(ValueError):
        Context().set_fact("   ", "Django")


def test_blank_role_is_rejected() -> None:
    with pytest.raises(ValueError):
        Context().as_message("   ")


def test_steps_are_windowed_when_max_steps_is_set() -> None:
    ctx = Context(steps=["opened docs", "opened errors"], max_steps=2)

    ctx.add_step("opened settings").set_max_steps(1)

    assert ctx.steps == ["opened settings"]


def test_trim_steps_can_clear_history_when_window_is_zero() -> None:
    ctx = Context(steps=["opened docs", "opened errors"], max_steps=0)

    assert ctx.steps == []

    ctx.extend_steps(["opened settings", "opened forms"])

    assert ctx.steps == []


def test_merge_facts_recursively_preserves_existing_nested_keys() -> None:
    ctx = Context(
        facts={
            "docs": {
                "product": "Django",
                "current_page": "settings reference",
            }
        }
    )

    ctx.merge_facts(
        {
            "docs": {
                "current_error": "ImproperlyConfigured",
                "current_page": "error reference",
            }
        }
    )

    assert ctx.facts == {
        "docs": {
            "product": "Django",
            "current_page": "error reference",
            "current_error": "ImproperlyConfigured",
        }
    }


def test_namespaced_fact_helpers_group_and_cleanup_related_state() -> None:
    ctx = Context()

    ctx.update_facts({"current_page": "settings reference"}, namespace="docs")
    ctx.set_fact("current_error", "ImproperlyConfigured", namespace="docs")

    removed = ctx.remove_fact("current_page", namespace="docs")

    assert removed == "settings reference"
    assert ctx.facts == {"docs": {"current_error": "ImproperlyConfigured"}}

    ctx.remove_fact("current_error", namespace="docs")

    assert ctx.facts == {}


def test_merge_combines_context_payloads_and_respects_step_window() -> None:
    ctx = Context(
        facts={"docs": {"product": "Django"}},
        steps=["opened docs"],
        intent={"task": {"name": "debug"}},
        scope={"session_id": "sess-123"},
        max_steps=2,
    )

    ctx.merge(
        {
            "facts": {"docs": {"current_page": "settings reference"}},
            "steps": ["opened errors", "opened settings"],
            "intent": {"task": {"confidence": 0.91}, "mode": "self-serve"},
            "scope": {"user_id": "user-123"},
        }
    )

    assert ctx.facts == {
        "docs": {
            "product": "Django",
            "current_page": "settings reference",
        }
    }
    assert ctx.steps == ["opened errors", "opened settings"]
    assert ctx.intent == {
        "task": {"name": "debug", "confidence": 0.91},
        "mode": "self-serve",
    }
    assert ctx.scope == {
        "session_id": "sess-123",
        "user_id": "user-123",
    }


def test_render_supports_scope_and_nested_values() -> None:
    text = Context(
        scope={"session_id": "sess-123"},
        facts={"docs": {"current_page": "settings reference"}},
        intent={"task": {"name": "debug", "confidence": 0.91}},
    ).render()

    assert text == (
        "Scope:\n"
        "  session id: sess-123\n\n"
        "Facts:\n"
        "  docs:\n"
        "    current page: settings reference\n\n"
        "Intent:\n"
        "  task:\n"
        "    name: debug\n"
        "    confidence: 0.91"
    )


def test_namespaced_fact_operations_require_mapping_namespace() -> None:
    ctx = Context(facts={"docs": "settings reference"})

    with pytest.raises(TypeError):
        ctx.set_fact("current_page", "forms reference", namespace="docs")


def test_negative_max_steps_is_rejected() -> None:
    with pytest.raises(ValueError):
        Context(max_steps=-1)
