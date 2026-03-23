import pytest
from pydantic import ValidationError

from flowstate import Context, ContextSchema


class StringOnlyFactsSchema(ContextSchema):
    facts: dict[str, str]


def test_context_schema_rejects_blank_step() -> None:
    with pytest.raises(ValidationError):
        ContextSchema(steps=["   "])


def test_context_schema_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ContextSchema(
            facts={},
            steps=[],
            intent={},
            actions=["refund"],
        )


def test_custom_schema_can_constrain_fact_values() -> None:
    ctx = Context(facts={"product": 123})

    with pytest.raises(ValidationError):
        ctx.validate(StringOnlyFactsSchema)
