# test_utils.py

import re
import typing as t

import pytest

# Assuming rule_engine package structure
# Adjust if your structure is different (e.g., rule_engine.rule, rule_engine.utils)
from rule_engine.rule import AND, Rule
from rule_engine.utils import JSONSchema, rule_to_schema

# --- Test Cases ---


def test_empty_rule() -> None:
    """An empty rule evaluates True, schema should match anything."""
    rule: Rule = Rule()
    expected_schema: JSONSchema = {}
    assert rule_to_schema(rule) == expected_schema


def test_negated_empty_rule() -> None:
    """A negated empty rule evaluates False, schema should match nothing."""
    rule: Rule = ~Rule()
    # 'not {}' is the standard way to represent a schema that matches nothing
    expected_schema: JSONSchema = {"not": {}}
    assert rule_to_schema(rule) == expected_schema


# --- Simple Conditions (Single Dict) ---


def test_simple_eq() -> None:
    rule: Rule = Rule(name="John")  # Default operator is EQ
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"name": {"type": "string", "const": "John"}},
        "required": ["name"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_eq_integer() -> None:
    rule: Rule = Rule(age=30)
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"age": {"type": "integer", "const": 30}},
        "required": ["age"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_eq_boolean() -> None:
    rule: Rule = Rule(active=True)
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"active": {"type": "boolean", "const": True}},
        "required": ["active"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_eq_null() -> None:
    rule: Rule = Rule(nullable_field=None)
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"nullable_field": {"type": "null", "const": None}},
        "required": ["nullable_field"],
    }
    assert rule_to_schema(rule) == expected_schema


# --- Start: Added tests for _schema_exact coverage ---
def test_simple_eq_float() -> None:
    # Covers line 131 in _schema_exact
    rule: Rule = Rule(score=98.6)
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"score": {"type": "number", "const": 98.6}},
        "required": ["score"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_eq_list() -> None:
    # Covers line 135 in _schema_exact
    rule: Rule = Rule(tags=["a", "b"])
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"tags": {"type": "array", "const": ["a", "b"]}},
        "required": ["tags"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_eq_dict() -> None:
    # Covers line 137 in _schema_exact
    rule: Rule = Rule(meta={"key": "value"})
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"meta": {"type": "object", "const": {"key": "value"}}},
        "required": ["meta"],
    }
    assert rule_to_schema(rule) == expected_schema


# --- End: Added tests for _schema_exact coverage ---


def test_simple_ne() -> None:
    rule: Rule = Rule(status__ne="inactive")
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"status": {"not": {"type": "string", "const": "inactive"}}},
        "required": ["status"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_gt() -> None:
    rule: Rule = Rule(score__gt=85.5)
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"score": {"type": "number", "exclusiveMinimum": 85.5}},
        "required": ["score"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_gte() -> None:
    rule: Rule = Rule(age__gte=21)
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"age": {"type": "number", "minimum": 21}},
        "required": ["age"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_lt() -> None:
    rule: Rule = Rule(risk__lt=0.1)
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"risk": {"type": "number", "exclusiveMaximum": 0.1}},
        "required": ["risk"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_lte() -> None:
    rule: Rule = Rule(count__lte=100)
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"count": {"type": "number", "maximum": 100}},
        "required": ["count"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_in_string() -> None:
    # Covers line 71 in _schema_in
    rule: Rule = Rule(tag__in=["urgent", "critical"])
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"tag": {"type": "string", "enum": ["urgent", "critical"]}},
        "required": ["tag"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_in_integer() -> None:
    # Covers line 75 in _schema_in
    rule: Rule = Rule(code__in=[404, 500, 503])
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"code": {"type": "integer", "enum": [404, 500, 503]}},
        "required": ["code"],
    }
    assert rule_to_schema(rule) == expected_schema


# --- Start: Added tests for _schema_in type inference coverage ---
def test_simple_in_boolean() -> None:
    # Covers line 73 in _schema_in
    rule: Rule = Rule(flag__in=[True, False])
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"flag": {"type": "boolean", "enum": [True, False]}},
        "required": ["flag"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_in_float() -> None:
    # Covers line 77 in _schema_in
    rule: Rule = Rule(value__in=[1.1, 2.2])
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"value": {"type": "number", "enum": [1.1, 2.2]}},
        "required": ["value"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_in_list() -> None:
    # Covers line 79 in _schema_in
    rule: Rule = Rule(value__in=[[1], [2]])
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"value": {"type": "array", "enum": [[1], [2]]}},
        "required": ["value"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_in_dict() -> None:
    # Covers line 81 in _schema_in
    rule: Rule = Rule(value__in=[{"a": 1}, {"b": 2}])
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"value": {"type": "object", "enum": [{"a": 1}, {"b": 2}]}},
        "required": ["value"],
    }
    assert rule_to_schema(rule) == expected_schema


# --- End: Added tests for _schema_in type inference coverage ---


def test_simple_in_mixed_types() -> None:
    # JSON Schema enum allows mixed types, though often not best practice
    rule: Rule = Rule(value__in=["a", 1, True, None])
    # Type inference picks the first one, but enum lists all
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"value": {"type": "string", "enum": ["a", 1, True, None]}},
        "required": ["value"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_in_empty_list() -> None:
    # An empty enum means nothing can match
    rule: Rule = Rule(value__in=[])
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"value": {"enum": []}},  # Type cannot be inferred
        "required": ["value"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_nin() -> None:
    rule: Rule = Rule(status__nin=["archived", "deleted"])
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"status": {"not": {"type": "string", "enum": ["archived", "deleted"]}}},
        "required": ["status"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_startswith() -> None:
    rule: Rule = Rule(sku__startswith="PROD-")
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"sku": {"type": "string", "pattern": "^PROD\\-"}},  # Escaped hyphen
        "required": ["sku"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_endswith() -> None:
    rule: Rule = Rule(filename__endswith=".txt")
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"filename": {"type": "string", "pattern": "\\.txt$"}},  # Escaped dot
        "required": ["filename"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_contains() -> None:
    rule: Rule = Rule(description__contains="important")
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"description": {"type": "string", "pattern": "important"}},
        "required": ["description"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_regex() -> None:
    rule: Rule = Rule(email__regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"email": {"type": "string", "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"}},
        "required": ["email"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_regex_compiled() -> None:
    pattern: t.Pattern[str] = re.compile(r"^\d{3}-\d{2}-\d{4}$")
    rule: Rule = Rule(ssn__regex=pattern)
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"ssn": {"type": "string", "pattern": r"^\d{3}-\d{2}-\d{4}$"}},
        "required": ["ssn"],
    }
    assert rule_to_schema(rule) == expected_schema


def test_simple_is() -> None:
    # 'is' is approximated by 'const'
    rule: Rule = Rule(flag__is=True)
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"flag": {"type": "boolean", "const": True}},
        "required": ["flag"],
    }
    assert rule_to_schema(rule) == expected_schema


# --- Approximated Case-Insensitive Operator Tests ---


def test_simple_iexact_approx() -> None:
    """iexact is approximated by exact ('const')."""
    rule_i: Rule = Rule(field__iexact="Value")
    rule_sens: Rule = Rule(field__exact="Value")
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"field": {"type": "string", "const": "Value"}},
        "required": ["field"],
    }
    assert rule_to_schema(rule_i) == expected_schema
    assert rule_to_schema(rule_sens) == expected_schema  # Should be same


def test_simple_istartswith_approx() -> None:
    """istartswith is approximated by startswith."""
    rule_i: Rule = Rule(field__istartswith="Prefix")
    rule_sens: Rule = Rule(field__startswith="Prefix")
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"field": {"type": "string", "pattern": "^Prefix"}},
        "required": ["field"],
    }
    assert rule_to_schema(rule_i) == expected_schema
    assert rule_to_schema(rule_sens) == expected_schema  # Should be same


def test_simple_iendswith_approx() -> None:
    """iendswith is approximated by endswith."""
    rule_i: Rule = Rule(field__iendswith="Suffix")
    rule_sens: Rule = Rule(field__endswith="Suffix")
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"field": {"type": "string", "pattern": "Suffix$"}},
        "required": ["field"],
    }
    assert rule_to_schema(rule_i) == expected_schema
    assert rule_to_schema(rule_sens) == expected_schema  # Should be same


def test_simple_icontains_approx() -> None:
    """icontains is approximated by contains (string)."""
    rule_i: Rule = Rule(field__icontains="Middle")
    rule_sens: Rule = Rule(field__contains="Middle")
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"field": {"type": "string", "pattern": "Middle"}},
        "required": ["field"],
    }
    assert rule_to_schema(rule_i) == expected_schema
    assert rule_to_schema(rule_sens) == expected_schema  # Should be same


def test_simple_iin_approx() -> None:
    """iin is approximated by in (requires list)."""
    rule_i: Rule = Rule(field__iin=["A", "B"])
    rule_sens: Rule = Rule(field__in=["A", "B"])
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"field": {"type": "string", "enum": ["A", "B"]}},
        "required": ["field"],
    }
    assert rule_to_schema(rule_i) == expected_schema
    assert rule_to_schema(rule_sens) == expected_schema  # Should be same


def test_simple_inin_approx() -> None:
    """inin is approximated by nin (requires list)."""
    rule_i: Rule = Rule(field__inin=["A", "B"])
    rule_sens: Rule = Rule(field__nin=["A", "B"])
    expected_schema: JSONSchema = {
        "type": "object",
        "properties": {"field": {"not": {"type": "string", "enum": ["A", "B"]}}},
        "required": ["field"],
    }
    assert rule_to_schema(rule_i) == expected_schema
    assert rule_to_schema(rule_sens) == expected_schema  # Should be same


# --- NotSet Operator ---


def test_notset_true() -> None:
    """Field must not be present."""
    rule: Rule = Rule(optional_field__notset=True)
    expected_schema: JSONSchema = {"not": {"required": ["optional_field"]}}
    assert rule_to_schema(rule) == expected_schema


def test_notset_false() -> None:
    """Field must be present."""
    rule: Rule = Rule(required_field__notset=False)
    expected_schema: JSONSchema = {"required": ["required_field"]}
    assert rule_to_schema(rule) == expected_schema


def test_notset_true_and_other_condition_or() -> None:
    """Test 'notset=True' combined with OR"""
    rule: Rule = Rule(optional__notset=True) | Rule(status="active")
    schema: JSONSchema = rule_to_schema(rule)
    expected_schema: JSONSchema = {
        "anyOf": [
            {"not": {"required": ["optional"]}},
            {
                "type": "object",
                "properties": {"status": {"const": "active", "type": "string"}},
                "required": ["status"],
            },
        ]
    }
    assert schema == expected_schema


def test_notset_false_and_other_condition_or() -> None:
    """Test 'notset=False' combined with OR"""
    rule: Rule = Rule(required__notset=False) | Rule(status="active")
    schema: JSONSchema = rule_to_schema(rule)
    expected_schema: JSONSchema = {
        "anyOf": [
            {"required": ["required"]},
            {
                "type": "object",
                "properties": {"status": {"const": "active", "type": "string"}},
                "required": ["status"],
            },
        ]
    }
    assert schema == expected_schema


def test_notset_true_and_other_condition_and() -> None:
    """Test 'notset=True' combined with AND"""
    # Rule: name == "X" AND optional is not set
    rule: Rule = Rule(name="X", optional__notset=True)
    schema: JSONSchema = rule_to_schema(rule)
    # Combined using allOf
    expected_schema: JSONSchema = {
        "allOf": [
            {
                "type": "object",
                "properties": {"name": {"const": "X", "type": "string"}},
                "required": ["name"],
            },
            {"not": {"required": ["optional"]}},
        ]
    }
    # The _dict_conditions_to_schema merges these into a single allOf
    assert schema == expected_schema


def test_notset_false_and_other_condition_and() -> None:
    """Test 'notset=False' combined with AND"""
    # Rule: name == "X" AND required is set
    rule: Rule = Rule(name="X", required__notset=False)
    schema: JSONSchema = rule_to_schema(rule)
    expected_schema: JSONSchema = {
        "allOf": [
            {
                "type": "object",
                "properties": {"name": {"const": "X", "type": "string"}},
                "required": ["name"],
            },
            {"required": ["required"]},
        ]
    }
    assert schema == expected_schema


# --- Multiple Conditions in Dict (Implicit AND) ---


def test_implicit_and_multiple_conditions() -> None:
    rule: Rule = Rule(name="Alice", age__gte=30, status__ne="inactive")
    expected_schema: JSONSchema = {
        "allOf": [
            {"type": "object", "properties": {"name": {"type": "string", "const": "Alice"}}, "required": ["name"]},
            {"type": "object", "properties": {"age": {"type": "number", "minimum": 30}}, "required": ["age"]},
            {
                "type": "object",
                "properties": {"status": {"not": {"type": "string", "const": "inactive"}}},
                "required": ["status"],
            },
        ]
    }
    assert rule_to_schema(rule) == expected_schema


# --- Explicit Combinations (&, |) ---


def test_explicit_and() -> None:
    rule: Rule = Rule(name="Bob") & Rule(age__lt=25)
    schema: JSONSchema = rule_to_schema(rule)
    # The structure generated might have nested allOf, let's check essentials
    assert "allOf" in schema
    assert isinstance(schema.get("allOf"), list)
    all_of_list: t.List[JSONSchema] = schema["allOf"]
    assert len(all_of_list) == 2

    # Check if the individual parts exist (order doesn't matter in allOf)
    expected_part1: JSONSchema = {
        "type": "object",
        "properties": {"name": {"type": "string", "const": "Bob"}},
        "required": ["name"],
    }
    expected_part2: JSONSchema = {
        "type": "object",
        "properties": {"age": {"type": "number", "exclusiveMaximum": 25}},
        "required": ["age"],
    }
    assert expected_part1 in all_of_list
    assert expected_part2 in all_of_list


# --- Start: Added tests for schema merge coverage ---
def test_merge_and_flattening() -> None:
    # Covers line 206 in _merge_schemas_and
    # (A & B) & C -> Creates Rule(Rule(A, B), C)
    # Inner Rule(A, B) generates {"allOf": [schema_A, schema_B]}
    # Outer Rule combines this with schema_C using AND
    # _merge_schemas_and should flatten this to {"allOf": [schema_A, schema_B, schema_C]}
    rule = (Rule(a=1) & Rule(b=2)) & Rule(c=3)
    schema = rule_to_schema(rule)

    assert "allOf" in schema
    assert isinstance(schema.get("allOf"), list)
    all_of_list: t.List[JSONSchema] = schema["allOf"]
    # Check essential structure - it should be flattened
    assert len(all_of_list) == 3
    assert {"type": "object", "properties": {"a": {"type": "integer", "const": 1}}, "required": ["a"]} in all_of_list
    assert {"type": "object", "properties": {"b": {"type": "integer", "const": 2}}, "required": ["b"]} in all_of_list
    assert {"type": "object", "properties": {"c": {"type": "integer", "const": 3}}, "required": ["c"]} in all_of_list


def test_merge_or_flattening() -> None:
    # Covers line 233 in _merge_schemas_or
    # (A | B) | C -> Creates Rule(Rule(A) | Rule(B)) | Rule(C)
    # Inner Rule(A) | Rule(B) generates {"anyOf": [schema_A, schema_B]}
    # Outer | combines this with schema_C using OR
    # _merge_schemas_or should flatten this to {"anyOf": [schema_A, schema_B, schema_C]}
    rule = (Rule(a=1) | Rule(b=2)) | Rule(c=3)
    schema = rule_to_schema(rule)

    assert "anyOf" in schema
    assert isinstance(schema.get("anyOf"), list)
    any_of_list: t.List[JSONSchema] = schema["anyOf"]
    # Check essential structure - it should be flattened
    assert len(any_of_list) == 3
    assert {"type": "object", "properties": {"a": {"type": "integer", "const": 1}}, "required": ["a"]} in any_of_list
    assert {"type": "object", "properties": {"b": {"type": "integer", "const": 2}}, "required": ["b"]} in any_of_list
    assert {"type": "object", "properties": {"c": {"type": "integer", "const": 3}}, "required": ["c"]} in any_of_list


def test_merge_or_only_not_schemas() -> None:
    # Covers line 219 in _merge_schemas_or
    # Rule that evaluates to "not anything" OR "not anything"
    # Example: field must not exist OR field must not exist
    rule = Rule(field__notset=True) | Rule(field__notset=True)
    schema = rule_to_schema(rule)
    # ORing two identical 'not required' results in the same 'not required'
    # Let's try a different approach: ORing two rules that inherently match nothing.
    # Rule() is {}, ~Rule() is {"not": {}}
    rule_match_nothing = ~Rule()  # Represents {"not": {}}
    combined_rule = rule_match_nothing | rule_match_nothing
    schema = rule_to_schema(combined_rule)
    # anyOf [{"not": {}}, {"not": {}}] simplifies to {"not": {}}
    assert schema == {"not": {}}


# --- End: Added tests for schema merge coverage ---


def test_explicit_or() -> None:
    rule: Rule = Rule(status="active") | Rule(priority__gte=5)
    schema: JSONSchema = rule_to_schema(rule)
    expected_schema: JSONSchema = {
        "anyOf": [
            {"type": "object", "properties": {"status": {"type": "string", "const": "active"}}, "required": ["status"]},
            {"type": "object", "properties": {"priority": {"type": "number", "minimum": 5}}, "required": ["priority"]},
        ]
    }
    assert schema == expected_schema


def test_mixed_and_or() -> None:
    # (name == "A" AND age > 10) OR status == "pending"
    rule: Rule = (Rule(name="A") & Rule(age__gt=10)) | Rule(status="pending")
    schema: JSONSchema = rule_to_schema(rule)

    expected_schema: JSONSchema = {
        "anyOf": [
            {  # Schema for (A & B)
                "allOf": [
                    {"type": "object", "properties": {"name": {"type": "string", "const": "A"}}, "required": ["name"]},
                    {
                        "type": "object",
                        "properties": {"age": {"type": "number", "exclusiveMinimum": 10}},
                        "required": ["age"],
                    },
                ]
            },
            {  # Schema for C
                "type": "object",
                "properties": {"status": {"type": "string", "const": "pending"}},
                "required": ["status"],
            },
        ]
    }
    assert schema == expected_schema


def test_mixed_or_and() -> None:
    # name == "A" OR (age > 10 AND status == "pending")
    rule: Rule = Rule(name="A") | (Rule(age__gt=10) & Rule(status="pending"))
    schema: JSONSchema = rule_to_schema(rule)

    expected_schema: JSONSchema = {
        "anyOf": [
            {  # Schema for A
                "type": "object",
                "properties": {"name": {"type": "string", "const": "A"}},
                "required": ["name"],
            },
            {  # Schema for (B & C)
                "allOf": [
                    {
                        "type": "object",
                        "properties": {"age": {"type": "number", "exclusiveMinimum": 10}},
                        "required": ["age"],
                    },
                    {
                        "type": "object",
                        "properties": {"status": {"type": "string", "const": "pending"}},
                        "required": ["status"],
                    },
                ]
            },
        ]
    }
    assert schema == expected_schema


def test_complex_grouping() -> None:
    # (A OR B) AND (C OR D)
    rule: Rule = (Rule(a=1) | Rule(b=2)) & (Rule(c=3) | Rule(d=4))
    schema: JSONSchema = rule_to_schema(rule)

    # Deep comparison needed, assert structure
    assert "allOf" in schema
    assert isinstance(schema.get("allOf"), list)
    all_of_list: t.List[JSONSchema] = schema["allOf"]
    assert len(all_of_list) == 2

    part1: JSONSchema = all_of_list[0]
    part2: JSONSchema = all_of_list[1]

    # Define expected parts
    expected_anyof_ab: JSONSchema = {
        "anyOf": [
            {"type": "object", "properties": {"a": {"type": "integer", "const": 1}}, "required": ["a"]},
            {"type": "object", "properties": {"b": {"type": "integer", "const": 2}}, "required": ["b"]},
        ]
    }
    expected_anyof_cd: JSONSchema = {
        "anyOf": [
            {"type": "object", "properties": {"c": {"type": "integer", "const": 3}}, "required": ["c"]},
            {"type": "object", "properties": {"d": {"type": "integer", "const": 4}}, "required": ["d"]},
        ]
    }

    # Check if the expected structures are present in the allOf list (order-independent)
    assert (part1 == expected_anyof_ab and part2 == expected_anyof_cd) or (
        part1 == expected_anyof_cd and part2 == expected_anyof_ab
    )


# --- Negation (~) ---


def test_negation_simple() -> None:
    rule: Rule = ~Rule(name="John")
    expected_schema: JSONSchema = {
        "not": {"type": "object", "properties": {"name": {"type": "string", "const": "John"}}, "required": ["name"]}
    }
    assert rule_to_schema(rule) == expected_schema


def test_negation_of_and() -> None:
    # NOT (name == "A" AND age > 10)
    rule: Rule = ~(Rule(name="A") & Rule(age__gt=10))
    schema: JSONSchema = rule_to_schema(rule)
    expected_inner_schema: JSONSchema = {
        "allOf": [
            {"type": "object", "properties": {"name": {"type": "string", "const": "A"}}, "required": ["name"]},
            {"type": "object", "properties": {"age": {"type": "number", "exclusiveMinimum": 10}}, "required": ["age"]},
        ]
    }
    assert schema == {"not": expected_inner_schema}


def test_negation_of_or() -> None:
    # NOT (status == "active" OR priority >= 5)
    rule: Rule = ~(Rule(status="active") | Rule(priority__gte=5))
    schema: JSONSchema = rule_to_schema(rule)
    expected_inner_schema: JSONSchema = {
        "anyOf": [
            {"type": "object", "properties": {"status": {"type": "string", "const": "active"}}, "required": ["status"]},
            {"type": "object", "properties": {"priority": {"type": "number", "minimum": 5}}, "required": ["priority"]},
        ]
    }
    assert schema == {"not": expected_inner_schema}


def test_double_negation() -> None:
    rule: Rule = ~~Rule(name="John")
    expected_schema: JSONSchema = {  # Negation cancels out
        "type": "object",
        "properties": {"name": {"type": "string", "const": "John"}},
        "required": ["name"],
    }
    assert rule_to_schema(rule) == expected_schema


# --- Error Handling ---


def test_invalid_operator_string() -> None:
    # Manually create a rule condition with an invalid op string
    rule: Rule = Rule()
    # Use t.cast to satisfy type checker for this specific manual setup
    rule._conditions = [(AND, t.cast(t.Union[Rule, t.Dict[str, t.Any]], {"field__invalidop": "value"}))]
    with pytest.raises(ValueError, match="Unsupported operator string: invalidop"):
        rule_to_schema(rule)


def test_invalid_notset_value() -> None:
    # Test that creating a rule with non-bool for notset raises error during schema gen
    with pytest.raises(ValueError, match="Operator 'notset' requires a boolean value"):
        # Need to wrap the call that processes the value
        rule_to_schema(Rule(field__notset="maybe"))


# Test type errors for operator values when calling rule_to_schema
@pytest.mark.parametrize(
    "op_str, invalid_value, expected_msg_part",
    [
        ("gte", "abc", "requires a numeric value"),
        ("gt", True, "requires a numeric value"),  # Should pass now
        ("lte", [], "requires a numeric value"),
        ("lt", {}, "requires a numeric value"),
        ("in", 123, "requires a list/tuple/set value"),
        ("nin", 45.6, "requires a list/tuple/set value"),
        ("iin", "abc", "requires a list/tuple/set value"),  # Test approx 'in' type check
        ("inin", "abc", "requires a list/tuple/set value"),  # Test approx 'nin' type check
        ("startswith", 123, "requires a string value"),
        ("endswith", None, "requires a string value"),
        ("contains", True, "requires a string value"),  # Test approx 'contains' type check (string only)
        ("regex", 123, "requires a string or regex pattern value"),
        ("istartswith", 123, "requires a string value"),  # Test approx 'startswith' type check
        ("iendswith", None, "requires a string value"),  # Test approx 'endswith' type check
        ("icontains", True, "requires a string value"),  # Test approx 'contains' type check (string only)
        # ('iexact', <complex object>, ...) - Difficult to test robustly for const
    ],
)
def test_operator_value_type_errors(op_str: str, invalid_value: t.Any, expected_msg_part: str) -> None:
    """Test that rule_to_schema raises TypeError/ValueError for invalid condition values."""
    kwargs: t.Dict[str, t.Any] = {f"field__{op_str}": invalid_value}
    rule: Rule = Rule(**kwargs)
    # Expect either TypeError or ValueError depending on the check
    # Match the specific error message structure from _translate_single_condition
    with pytest.raises(
        (TypeError, ValueError), match=f"Error processing condition for field 'field':.*{re.escape(expected_msg_part)}"
    ):
        rule_to_schema(rule)
