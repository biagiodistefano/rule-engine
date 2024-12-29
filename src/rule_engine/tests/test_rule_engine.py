import json
import typing as t

import pytest

from rule_engine.rule import NOT_SET, OPERATOR_FUNCTIONS, EvaluationResult, Operator, Rule, RuleJSONEncoder, evaluate


@pytest.mark.parametrize(
    "operator, field_value, condition_value, expected",
    [
        (Operator.GTE, 5, 3, True),
        (Operator.GTE, 3, 5, False),
        (Operator.GT, 5, 3, True),
        (Operator.GT, 3, 5, False),
        (Operator.LTE, 3, 5, True),
        (Operator.LTE, 5, 3, False),
        (Operator.LT, 3, 5, True),
        (Operator.LT, 5, 3, False),
        (Operator.IN, "a", ["a", "b"], True),
        (Operator.IN, "c", ["a", "b"], False),
        (Operator.NIN, "a", ["c", "d"], True),
        (Operator.NIN, "a", ["a", "b"], False),
        (Operator.IIN, "Hello", ["hello", "world"], True),
        (Operator.IIN, "hello", ["Hello", "world"], True),
        (Operator.IIN, "hello", ["world", "foo"], False),
        (Operator.IIN, "hello", "Hello world", True),
        (Operator.ININ, "hello", ["world", "foo"], True),
        (Operator.ININ, "hello", ["world", "hello"], False),
        (Operator.STARTSWITH, "hello", "he", True),
        (Operator.STARTSWITH, "hello", "lo", False),
        (Operator.ISTARTSWITH, "hello", "HE", True),
        (Operator.ENDSWITH, "hello", "lo", True),
        (Operator.ENDSWITH, "hello", "he", False),
        (Operator.IENDSWITH, "hello", "LO", True),
        (Operator.CONTAINS, [1, 2, 3], 2, True),
        (Operator.CONTAINS, [1, 2, 3], 4, False),
        (Operator.CONTAINS, "Hello", "ell", True),
        (Operator.ICONTAINS, "Hello", "ell", True),
        (Operator.ICONTAINS, "Hello", "ELL", True),
        (Operator.EXACT, "foo", "foo", True),
        (Operator.EXACT, "foo", "bar", False),
        (Operator.IS, 3, 3, True),
        (Operator.IS, 3, 4, False),
        (Operator.IEXACT, "foo", "FOO", True),
        (Operator.NE, 3, 4, True),
        (Operator.NE, 3, 3, False),
        (Operator.EQ, 3, 3, True),
        (Operator.EQ, 3, 4, False),
        (Operator.REGEX, "hello123", r"\w+\d+", True),
        (Operator.REGEX, "hello", r"\d+", False),
        # (Operator.FUNC, "hello", lambda x: x.startswith("he"), True),
        # (Operator.FUNC, "hello", lambda x: x.endswith("lo"), True),
    ],
)
def test_operator_evaluation(operator: str, field_value: t.Any, condition_value: t.Any, expected: bool) -> None:
    assert OPERATOR_FUNCTIONS[operator](field_value, condition_value) == expected


@pytest.mark.parametrize(
    "operator, field_value, condition_value",
    (
        (Operator.STARTSWITH, 5, "hello"),
        (Operator.ENDSWITH, "hello", 5),
        (Operator.REGEX, 5, "hello"),
        # (Operator.FUNC, 5, "hello"),
    ),
)
def test_operator_evaluation_value_error(operator: str, field_value: t.Any, condition_value: t.Any) -> None:
    with pytest.raises(ValueError):
        OPERATOR_FUNCTIONS[operator](field_value, condition_value)


@pytest.mark.parametrize(
    "conditions, example, expected",
    [
        ({"name": "John"}, {"name": "John"}, True),
        ({"name": "John"}, {"name": "Jane"}, False),
        ({"age__gte": 21}, {"age": 22}, True),
        ({"age__gte": 21}, {"age": 18}, False),
    ],
)
def test_simple_rule_evaluation(conditions: dict[str, t.Any], example: dict[str, t.Any], expected: bool) -> None:
    rule = Rule(**conditions)
    assert bool(evaluate(rule, example)) is expected


def test_nested_rules() -> None:
    rule = Rule(
        Rule(name="John") & Rule(age__gte=21) | (Rule(name="Jane") & Rule(age__lt=22)),
    )

    example_true = {"name": "John", "age": 25}
    example_false = {"name": "Jane", "age": 21}
    assert evaluate(rule, example_true)
    assert evaluate(rule, example_false)


def test_negation() -> None:
    rule = ~Rule(name="John")
    example_true = {"name": "Jane"}
    example_false = {"name": "John"}
    assert evaluate(rule, example_true)
    assert not evaluate(rule, example_false)


def test_invalid_rule_construction() -> None:
    with pytest.raises(ValueError):
        Rule("invalid argument")  # type: ignore[arg-type]


def test_combined_rules() -> None:
    rule1 = Rule(name="John")
    rule2 = Rule(age__gte=21)

    combined_and = rule1 & rule2
    combined_or = rule1 | rule2

    example_true_and = {"name": "John", "age": 22}
    example_false_and = {"name": "Jane", "age": 22}
    example_true_or = {"name": "Jane", "age": 22}

    assert evaluate(combined_and, example_true_and)
    assert not evaluate(combined_and, example_false_and)
    assert evaluate(combined_or, example_true_or)


@pytest.mark.parametrize(
    "rule_id, valid",
    [
        ("valid-id_123", True),
        ("", False),
        ("a" * 65, False),
        ("valid-id", True),
    ],
)
def test_id_validation(rule_id: str, valid: bool) -> None:
    if valid:
        rule = Rule()
        rule.id = rule_id
        assert rule.id == rule_id
    else:
        with pytest.raises(ValueError):
            rule = Rule()
            rule.id = rule_id


def test_rule_repr() -> None:
    rule = Rule(name="John", age__gte=21)
    expected_repr = "Rule(conditions=[('AND', {'name': 'John', 'age__gte': 21})], negated=False)"
    assert repr(rule) == expected_repr


def test_empty_conditions() -> None:
    rule = Rule()
    example = {"any_field": "any_value"}
    assert evaluate(rule, example)


def test_validate_id_value_error() -> None:
    with pytest.raises(ValueError):
        Rule._validate_id(42)  # type: ignore[arg-type]


def test_evaluate_operator_value_error() -> None:
    with pytest.raises(ValueError):
        Rule()._evaluate_operator("invalid_operator", "field_value", "condition_value", "key")


def test_and_value_error() -> None:
    with pytest.raises(ValueError):
        Rule() & "invalid_rule"  # type: ignore[operator]


def test_or_value_error() -> None:
    with pytest.raises(ValueError):
        Rule() | "invalid_rule"  # type: ignore[operator]


def test_to_json_and_from_json() -> None:
    rule = Rule(Rule(foo="bar") | Rule(foo="baz"), name="John", age__gte=21)
    rule_json = rule.to_json()
    loaded_rule = Rule.from_json(rule_json)
    assert rule.to_dict() == loaded_rule.to_dict()
    example_true = {"foo": "bar", "name": "John", "age": 22}
    example_false = {"foo": "qux", "name": "Jane", "age": 19}
    assert evaluate(rule, example_true)
    assert not evaluate(rule, example_false)
    assert evaluate(loaded_rule, example_true)
    assert not evaluate(loaded_rule, example_false)


def test_to_load_rule_invalid() -> None:
    rule = Rule(Rule(foo="bar"))
    rule_json = rule.to_dict()
    rule_json.pop("$rule")
    with pytest.raises(ValueError):
        Rule.from_dict(rule_json)


def test_res_and_value_error() -> None:
    result = EvaluationResult()
    with pytest.raises(ValueError):
        result & "invalid_res"  # type: ignore[operator]


def test_res_or_value_error() -> None:
    result = EvaluationResult()
    with pytest.raises(ValueError):
        result | "invalid_res"  # type: ignore[operator]


def test_result_to_json() -> None:
    rule = Rule(name="John") & Rule(age__gte=21) | Rule(name="Jane")
    example = {"name": "John", "age": 22}
    res = evaluate(rule, example)
    assert (
        res.to_json()
        == """{"field": "name", "value": "John", "operator": "eq", "condition_value": "John", "result": true, "negated": false, "children": [["AND", {"field": "age", "value": 22, "operator": "gte", "condition_value": 21, "result": true, "negated": false, "children": []}], ["OR", {"field": "name", "value": "John", "operator": "eq", "condition_value": "Jane", "result": false, "negated": false, "children": []}]]}"""  # noqa: E501
    )


@pytest.mark.parametrize(
    ("data", "condition_value"),
    [
        ({"foo": 7}, "bar"),
        ({"foo": "bar"}, 7),
        ({"foo": "bar"}, ["bar", 7]),
    ],
)
def test_iin_value_error(data: dict[str, t.Any], condition_value: t.Any) -> None:
    with pytest.raises(ValueError):
        rule = Rule(foo__iin=condition_value)
        evaluate(rule, data)


@pytest.mark.parametrize(
    ("data", "rule", "expected_result"),
    [
        ({}, Rule(whatever__gte=3), False),
        ({}, Rule(name__iin=["John", "Jane"]), False),
        ({}, Rule(name__notset=True), True),
        ({"name": "Frank"}, Rule(name__notset=True), False),
        ({"name": "Frank"}, Rule(name__notset=False), True),
    ],
)
def test_not_set(data: dict[str, t.Any], rule: Rule, expected_result: bool) -> None:
    assert bool(evaluate(rule, data)) is expected_result


def test_raise_on_not_set() -> None:
    rule = Rule(foo="bar", __raise_on_notset=True)
    with pytest.raises(ValueError):
        rule.evaluate({})


@pytest.mark.parametrize(
    ("input_data", "expected_value", "expected_result"),
    [
        ({"no-field-match": "not-set"}, None, False),  # NOT_SET case
        ({"field_match": "is-set"}, "is-set", True),   # Normal case
    ],
)
def test_regression_not_set_json_serialization(
    input_data: dict[str, str],
    expected_value: str | None,
    expected_result: bool,
) -> None:
    """Test that NOT_SET is properly serialized to JSON as null."""
    rule = Rule(field_match__nin=["not-set"])
    result = rule.evaluate(input_data)

    # Test direct JSON serialization
    json_str = result.to_json()
    json_data = json.loads(json_str)
    assert json_data["value"] == expected_value

    # Verify the original evaluation result
    assert (result.value is NOT_SET) == (expected_value is None)
    assert bool(result) is expected_result


def test_rule_json_encoder() -> None:
    """Test RuleJSONEncoder handles both NOT_SET and regular objects."""
    encoder = RuleJSONEncoder()

    # Test NOT_SET encoding
    assert encoder.default(NOT_SET) is None

    # Test regular object falls back to default behavior
    with pytest.raises(TypeError):
        encoder.default(object())
