# Simple Rule Engine in Pure Python

[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/licenses/MIT)
[![Build](https://github.com/biagiodistefano/rule-engine/actions/workflows/main.yaml/badge.svg?branch=main)](https://github.com/biagiodistefano/rule-engine/actions/workflows/main.yaml)
[![codecov](https://codecov.io/github/biagiodistefano/rule-engine/graph/badge.svg?token=7G7X642DX0)](https://codecov.io/github/biagiodistefano/rule-engine)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/light-rule-engine)
![PyPI - Version](https://img.shields.io/pypi/v/light-rule-engine)


The **Simple Rule Engine** is a lightweight library for creating, combining, and evaluating (nested) rules. Inspired by Django's `Q` object, it allows you to construct complex logical conditions and evaluate them against dictionaries of data.

## Quickstart

```
pip install light-rule-engine
```

```python
from rule_engine import Rule, evaluate

# Rule: (foo == "bar" OR foo == "baz") AND (name == "John" AND age >= 21)
rule = Rule(
    Rule(foo="bar") | Rule(foo="baz"),
    name="John", age__gte=21
)

example_true = {"foo": "bar", "name": "John", "age": 22}
example_false = {"foo": "qux", "name": "Jane", "age": 19}

assert evaluate(rule, example_true)
assert not evaluate(rule, example_false)
```


## Features

- Create rules with simple conditions or nested logic.
- Combine rules using logical operators:
  - `&` (AND)
  - `|` (OR)
  - `~` (NOT)
- Evaluate rules against dictionaries of values.
- Supports a wide range of operators (listed below).
- Extensible: Add your own custom operators if needed.

---

## Installation

```bash
pip install light-rule-engine
```
```bash
poetry add light-rule-engine
```
```bash
uv add light-rule-engine
```

## Supported Operators

| **Operator**  | **Description**                                                |
|---------------|----------------------------------------------------------------|
| `gte`         | Greater than or equal to                                       |
| `gt`          | Greater than                                                   |
| `lte`         | Less than or equal to                                          |
| `lt`          | Less than                                                      |
| `in`          | Value is in a list/collection                                  |
| `iin`         | Value is in a list/collection or string (case insensitive)     |
| `nin`         | Value is not in a list/collection                              |
| `inin`        | Value is not in a list/collection or string (case insensitive) |
| `startswith`  | String starts with a specific value                            |
| `istartswith` | String starts with a specific value (case-insensitive)         |
| `endswith`    | String ends with a specific value                              |
| `iendswith`   | String ends with a specific value (case-insensitive)           |
| `contains`    | Collection or string contains a specific value                 |
| `icontains`   | String contains a specific value (case-insensitive)            |
| `exact`       | Value matches exactly                                          |
| `iexact`      | Value matches exactly (case-insensitive)                       |
| `ne`          | Not equal                                                      |
| `eq`          | Equal to                                                       |
| `regex`       | Matches a regular expression pattern                           |
| `is`          | Identity comparison (evaluates with `is`)                      |
|`notset`       | Value is not set                                               |

---

## Basic Usage

### Creating Rules

Rules can be created using the `Rule` object. You can pass positional arguments (`*args`) for nested rules and keyword arguments (`**kwargs`) for conditions.

```python
from rule_engine import Rule

# Simple rule with conditions
rule = Rule(name="John", age__gte=21)

# Nested rules with logical operators
complex_rule = Rule(
    Rule(name="John") & Rule(age__gte=21),
    Rule(name="Jane") | Rule(age__lt=20)
)
```

### Logical Operators

- `&` (AND): Combines rules that must all be satisfied.
- `|` (OR): Combines rules where at least one must be satisfied.
- `~` (NOT): Negates a rule.

Example:

```python
from rule_engine import Rule

# Rule: (name == "John" AND age >= 21) OR (name == "Jane" AND age < 20)
rule = Rule(
    Rule(name="John") & Rule(age__gte=21) |
    Rule(name="Jane") & Rule(age__lt=20)
)
```

Alternatively, you can also express this in the following fashion:

```python
from rule_engine import Rule

rule = Rule(name="John", age__gte=21) | Rule(name="Jane", age__lt=20)
```

### Evaluating Rules
To evaluate a rule, use the evaluate function or the evaluate method of the rule. Provide a dictionary of data to check the rule against.

```python
from rule_engine import Rule, evaluate

# Rule: (foo == "bar" OR foo == "baz") AND (name == "John" AND age >= 21)
rule = Rule(
    Rule(foo="bar") | Rule(foo="baz"),
    name="John", age__gte=21
)

example_true = {"foo": "bar", "name": "John", "age": 22}
example_false = {"foo": "qux", "name": "Jane", "age": 19}

assert evaluate(rule, example_true)
assert not evaluate(rule, example_false)
```

## Advanced Usage

### Custom Operators

You can extend the rule engine by adding new operators.
Use the func operator for custom logic, or modify the `OPERATOR_FUNCTIONS` dictionary for persistent custom operators.

You can set a `Rule`'s id in two ways:

```python
from rule_engine import Rule

rule = Rule(name="John")
rule.id = "my-rule"
```

or

```python
from rule_engine import Rule

rule = Rule(name="John", __id="my-rule")
```

### Raise on Missing Fields

```python
from rule_engine import Rule

rule = Rule(name="John", age__gte=21, __raise_on_notset=True)

rule.evaluate({"name": "John"})
# >>> ValueError(f"Field 'age' is not set in the example data")
```

## Full example

```python
from rule_engine import Rule, evaluate

# Complex rule example
rule = Rule(
    Rule(credit_rating__gte=50, flood_risk__lt=10) |
    Rule(revenue__gt=1_000_000)
)

data = {"credit_rating": 55, "flood_risk": 5}
assert evaluate(rule, data)

data = {"revenue": 1_500_000}
assert evaluate(rule, data)

data = {"credit_rating": 40, "flood_risk": 15, "revenue": 500_000}
assert not evaluate(rule, data)
```

## The EvaluationResult object

The `evaluate` function returns an `EvaluationResult` object that contains the result of the evaluation and the rule that was evaluated.

It contains a granular representation of the evaluation process, including the result of each condition and the final result.

```python
from rule_engine import Rule, evaluate

rule = Rule(name="John") & Rule(age__gte=21) | Rule(name="Jane")
example = {"name": "John", "age": 22}
res = evaluate(rule, example)

print(bool(res))  # True
print(res.to_json(indent=2))  # to_dict() also available

"""
{
  "field": "name",
  "value": "John",
  "operator": "eq",
  "condition_value": "John",
  "result": true,
  "negated": false,
  "children": [
    [
      "AND",
      {
        "field": "age",
        "value": 22,
        "operator": "gte",
        "condition_value": 21,
        "result": true,
        "negated": false,
        "children": []
      }
    ],
    [
      "OR",
      {
        "field": "name",
        "value": "John",
        "operator": "eq",
        "condition_value": "Jane",
        "result": false,
        "negated": false,
        "children": []
      }
    ]
  ]
}
"""
```

## Contributing
Contributions are welcome! For feature requests, bug reports, or questions, please open an issue on GitHub.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements
This project was inspired by **Django's awesome** `Q` object and the need for a simple rule engine in Python.
