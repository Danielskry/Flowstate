from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy

from .schemas import ContextSchema


class Context:
    """Mutable grounding state for an agent.

    ``Context`` keeps four sections:

    - ``scope``: session, user, or tenant identifiers
    - ``facts``: durable known state
    - ``steps``: relevant observed progression
    - ``intent``: the current inferred goal

    ``steps`` can be bounded with ``max_steps`` to keep a rolling window.

    The same context can be rendered for an agent or inspected directly by
    deterministic application code.
    """

    def __init__(
        self,
        *,
        facts: Mapping[str, object] | None = None,
        steps: Iterable[str] | None = None,
        intent: Mapping[str, object] | None = None,
        scope: Mapping[str, object] | None = None,
        max_steps: int | None = None,
    ) -> None:
        self.facts: dict[str, object] = {}
        self.steps: list[str] = []
        self.intent: dict[str, object] = {}
        self.scope: dict[str, object] = {}
        self.max_steps = _normalize_max_steps(max_steps)

        if scope is not None:
            self.update_scope(scope)

        if facts is not None:
            self.update_facts(facts)
        if steps is not None:
            self.extend_steps(steps)
        if intent is not None:
            self.update_intent(intent)

    def set_fact(
        self,
        key: str,
        value: object,
        *,
        namespace: str | None = None,
    ) -> Context:
        """Set or replace a fact, optionally inside a namespace."""
        target = self._facts_namespace(namespace)
        target[_normalize_key(key)] = _clone_value(value)
        return self

    def update_facts(
        self,
        values: Mapping[str, object] | None = None,
        /,
        *,
        namespace: str | None = None,
        **kwargs: object,
    ) -> Context:
        """Set multiple facts on the current context."""
        if values is not None:
            for key, value in values.items():
                self.set_fact(key, value, namespace=namespace)
        for key, value in kwargs.items():
            self.set_fact(key, value, namespace=namespace)
        return self

    def merge_facts(
        self,
        values: Mapping[str, object] | None = None,
        /,
        *,
        namespace: str | None = None,
        **kwargs: object,
    ) -> Context:
        """Recursively merge facts into the current context."""
        target = self._facts_namespace(namespace)
        if values is not None:
            _merge_mapping(target, values)
        if kwargs:
            _merge_mapping(target, kwargs)
        return self

    def remove_fact(
        self,
        key: str,
        default: object | None = None,
        *,
        namespace: str | None = None,
    ) -> object | None:
        """Remove a fact and return its previous value if present."""
        target = self._existing_facts_namespace(namespace)
        if target is None:
            return default

        removed = target.pop(_normalize_key(key), default)
        self._cleanup_facts_namespace(namespace, target)
        return removed

    def clear_facts(self, *, namespace: str | None = None) -> Context:
        """Remove all facts, or remove an entire namespace."""
        if namespace is None:
            self.facts.clear()
            return self

        self.facts.pop(_normalize_namespace(namespace), None)
        return self

    def add_step(self, step: str) -> Context:
        """Append a human-readable step."""
        self.steps.append(_normalize_text(step, field_name="step"))
        self._trim_steps()
        return self

    def extend_steps(self, steps: Iterable[str]) -> Context:
        """Append multiple steps."""
        for step in steps:
            self.add_step(step)
        return self

    def pop_step(self, index: int = -1) -> str:
        """Remove and return a step, defaulting to the most recent one."""
        return self.steps.pop(index)

    def clear_steps(self) -> Context:
        """Remove all steps."""
        self.steps.clear()
        return self

    def set_max_steps(self, max_steps: int | None) -> Context:
        """Update the rolling window size used for steps."""
        self.max_steps = _normalize_max_steps(max_steps)
        self._trim_steps()
        return self

    def trim_steps(self, max_steps: int | None = None) -> Context:
        """Trim the step list in place, optionally updating the window size."""
        if max_steps is not None:
            self.max_steps = _normalize_max_steps(max_steps)
        self._trim_steps()
        return self

    def set_intent(self, key: str, value: object) -> Context:
        """Set or replace an intent field."""
        self.intent[_normalize_key(key)] = _clone_value(value)
        return self

    def update_intent(
        self,
        values: Mapping[str, object] | None = None,
        /,
        **kwargs: object,
    ) -> Context:
        """Set multiple intent fields on the current context."""
        if values is not None:
            for key, value in values.items():
                self.set_intent(key, value)
        for key, value in kwargs.items():
            self.set_intent(key, value)
        return self

    def merge_intent(
        self,
        values: Mapping[str, object] | None = None,
        /,
        **kwargs: object,
    ) -> Context:
        """Recursively merge intent fields into the current context."""
        if values is not None:
            _merge_mapping(self.intent, values)
        if kwargs:
            _merge_mapping(self.intent, kwargs)
        return self

    def remove_intent(self, key: str, default: object | None = None) -> object | None:
        """Remove an intent field and return its previous value if present."""
        return self.intent.pop(_normalize_key(key), default)

    def clear_intent(self) -> Context:
        """Remove all intent fields."""
        self.intent.clear()
        return self

    def set_scope(self, key: str, value: object) -> Context:
        """Set or replace a scope field such as user or session identifiers."""
        self.scope[_normalize_key(key)] = _clone_value(value)
        return self

    def update_scope(
        self,
        values: Mapping[str, object] | None = None,
        /,
        **kwargs: object,
    ) -> Context:
        """Set multiple scope fields on the current context."""
        if values is not None:
            for key, value in values.items():
                self.set_scope(key, value)
        for key, value in kwargs.items():
            self.set_scope(key, value)
        return self

    def merge_scope(
        self,
        values: Mapping[str, object] | None = None,
        /,
        **kwargs: object,
    ) -> Context:
        """Recursively merge scope fields into the current context."""
        if values is not None:
            _merge_mapping(self.scope, values)
        if kwargs:
            _merge_mapping(self.scope, kwargs)
        return self

    def remove_scope(self, key: str, default: object | None = None) -> object | None:
        """Remove a scope field and return its previous value if present."""
        return self.scope.pop(_normalize_key(key), default)

    def clear_scope(self) -> Context:
        """Remove all scope fields."""
        self.scope.clear()
        return self

    def clear(self) -> Context:
        """Reset the full context."""
        self.clear_facts()
        self.clear_steps()
        self.clear_intent()
        self.clear_scope()
        return self

    def merge(self, other: Context | ContextSchema | Mapping[str, object]) -> Context:
        """Merge another context payload into this instance."""
        payload = _coerce_context_payload(other)
        self.merge_scope(payload["scope"])
        self.merge_facts(payload["facts"])
        self.extend_steps(payload["steps"])
        self.merge_intent(payload["intent"])
        return self

    def render(self) -> str:
        """Render the current grounding state as plain text."""
        sections: list[str] = []

        scope_lines = _render_mapping(self.scope)
        if scope_lines:
            sections.append("Scope:\n" + "\n".join(scope_lines))

        fact_lines = _render_mapping(self.facts)
        if fact_lines:
            sections.append("Facts:\n" + "\n".join(fact_lines))

        step_lines = [f"  {step}" for step in self.steps]
        if step_lines:
            sections.append("Steps:\n" + "\n".join(step_lines))

        intent_lines = _render_mapping(self.intent)
        if intent_lines:
            sections.append("Intent:\n" + "\n".join(intent_lines))

        return "\n\n".join(sections)

    def read(self) -> str:
        """Alias for ``render()``."""
        return self.render()

    def as_message(self, role: str = "system") -> dict[str, str]:
        """Compile the current context into a chat message payload."""
        return {
            "role": _normalize_text(role, field_name="role"),
            "content": self.render(),
        }

    def to_dict(self) -> dict[str, object]:
        """Export the current context as plain Python data."""
        return {
            "facts": _clone_mapping(self.facts),
            "steps": list(self.steps),
            "intent": _clone_mapping(self.intent),
            "scope": _clone_mapping(self.scope),
            "max_steps": self.max_steps,
        }

    def to_schema(self) -> ContextSchema:
        """Export the current context into a validated Pydantic schema."""
        return ContextSchema(**self.to_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Context:
        """Build a context instance from a plain Python payload."""
        return cls.from_schema(ContextSchema.model_validate(data))

    @classmethod
    def from_schema(cls, schema: ContextSchema) -> Context:
        """Build a context instance from a validated Pydantic schema."""
        return cls(
            facts=schema.facts,
            steps=schema.steps,
            intent=schema.intent,
            scope=schema.scope,
            max_steps=schema.max_steps,
        )

    def validate(self, schema_cls: type[ContextSchema] | None = None) -> ContextSchema:
        """Validate the current context against ``ContextSchema`` or a subclass."""
        target_schema = schema_cls or ContextSchema
        return target_schema.model_validate(self.to_dict())

    def _facts_namespace(self, namespace: str | None) -> dict[str, object]:
        if namespace is None:
            return self.facts
        return _get_namespace_mapping(
            self.facts,
            namespace,
            create=True,
            field_name="facts",
        )

    def _existing_facts_namespace(self, namespace: str | None) -> dict[str, object] | None:
        if namespace is None:
            return self.facts
        return _get_namespace_mapping(
            self.facts,
            namespace,
            create=False,
            field_name="facts",
        )

    def _cleanup_facts_namespace(
        self,
        namespace: str | None,
        values: Mapping[str, object],
    ) -> None:
        if namespace is None or values:
            return
        self.facts.pop(_normalize_namespace(namespace), None)

    def _trim_steps(self) -> None:
        if self.max_steps is None:
            return

        overflow = len(self.steps) - self.max_steps
        if overflow > 0:
            del self.steps[:overflow]


def _normalize_key(value: str) -> str:
    return _normalize_text(value, field_name="key")


def _normalize_namespace(value: str) -> str:
    return _normalize_text(value, field_name="namespace")


def _normalize_max_steps(value: int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("max_steps must be an integer or None")
    if value < 0:
        raise ValueError("max_steps cannot be negative")
    return value


def _normalize_text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be blank")
    return normalized


def _clone_value(value: object) -> object:
    return deepcopy(value)


def _clone_mapping(values: Mapping[str, object]) -> dict[str, object]:
    return {key: _clone_value(value) for key, value in values.items()}


def _merge_mapping(target: dict[str, object], values: Mapping[str, object]) -> dict[str, object]:
    for key, value in values.items():
        normalized_key = _normalize_key(key)
        if isinstance(value, Mapping):
            existing = target.get(normalized_key)
            if isinstance(existing, Mapping):
                merged = _clone_mapping(existing)
                target[normalized_key] = _merge_mapping(merged, value)
            else:
                target[normalized_key] = _merge_mapping({}, value)
            continue

        target[normalized_key] = _clone_value(value)

    return target


def _coerce_context_payload(
    other: Context | ContextSchema | Mapping[str, object],
) -> dict[str, object]:
    if isinstance(other, Context):
        return other.to_dict()
    if isinstance(other, ContextSchema):
        return Context.from_schema(other).to_dict()
    return Context.from_dict(other).to_dict()


def _get_namespace_mapping(
    container: dict[str, object],
    namespace: str,
    *,
    create: bool,
    field_name: str,
) -> dict[str, object] | None:
    normalized = _normalize_namespace(namespace)
    existing = container.get(normalized)

    if existing is None:
        if not create:
            return None
        scoped: dict[str, object] = {}
        container[normalized] = scoped
        return scoped

    if not isinstance(existing, Mapping):
        raise TypeError(
            f"{field_name}.{normalized} must be a mapping to use namespace operations"
        )

    if isinstance(existing, dict):
        return existing

    scoped = _clone_mapping(existing)
    container[normalized] = scoped
    return scoped


def _render_mapping(values: Mapping[str, object], *, indent: int = 1) -> list[str]:
    lines: list[str] = []
    prefix = "  " * indent
    for key, value in values.items():
        label = str(key).replace("_", " ")
        lines.extend(_render_labeled_value(label, value, prefix=prefix, indent=indent))
    return lines


def _render_labeled_value(
    label: str,
    value: object,
    *,
    prefix: str,
    indent: int,
) -> list[str]:
    if isinstance(value, Mapping):
        mapping = _clone_mapping(value)
        if not mapping:
            return [f"{prefix}{label}: {{}}"]
        return [f"{prefix}{label}:"] + _render_mapping(mapping, indent=indent + 1)

    if _is_renderable_sequence(value):
        items = list(value)
        if not items:
            return [f"{prefix}{label}: []"]
        return [f"{prefix}{label}:"] + _render_sequence(items, indent=indent + 1)

    return [f"{prefix}{label}: {value}"]


def _render_sequence(values: Sequence[object], *, indent: int) -> list[str]:
    lines: list[str] = []
    prefix = "  " * indent

    for value in values:
        if isinstance(value, Mapping):
            mapping = _clone_mapping(value)
            if not mapping:
                lines.append(f"{prefix}- {{}}")
                continue
            lines.append(f"{prefix}-")
            lines.extend(_render_mapping(mapping, indent=indent + 1))
            continue

        if _is_renderable_sequence(value):
            items = list(value)
            if not items:
                lines.append(f"{prefix}- []")
                continue
            lines.append(f"{prefix}-")
            lines.extend(_render_sequence(items, indent=indent + 1))
            continue

        lines.append(f"{prefix}- {value}")

    return lines


def _is_renderable_sequence(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
