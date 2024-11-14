# Simple Rule engine in pure Python

This rule engine allows for the creation and combination of (nested) rules.

Inspired by the behavior of Django's `Q` object, this rule engine allows for the creation of complex rules that can be evaluated with a dictionary of values.

A `Rule` object is a class that can be initiated wit more `Rule` objects as positional `*args`
and `**kwargs` for additional conditions.

Supported operators are: `gte`, `lte`, `gt`, `lt`, `ne`, `in`, `contains`, `icontains`, `exact`, `iexact`, `startswith`, `endswith`.

More can be added if you are bored enough.

The `Rule` object can be combined with `&` (and), `|` (or). It can be negated with `~` (not).

The `Rule` object can be evaluated against a dictionary of values:

```python
from rule_engine import Rule, evaluate

r = Rule(
    Rule(foo="bar") | Rule(foo="baz"),
    name="John", age__gte=21
) | Rule(
    name="Jane", age__lt=20
)

example_true = {"foo": "bar", "name": "John", "age": 22}
print(evaluate(r, example_true))  # True
```

See `src/solution.py` for more examples.

The provided rule in the example would translate to:

```python
provided_rule = Rule(
    credit_rating__gt=50,
    flood_risk__lt=10,
) | Rule(revenue__gt=1_000_000)
# Rule(conditions=[('AND', Rule(conditions=[('AND', {'credit_rating__gt': 50, 'flood_risk__lt': 10})], negated=False)), ('OR', Rule(conditions=[('AND', {'revenue__gt': 1000000})], negated=False))], negated=False)
```

## TODOs:
- [ ] Add more operators
- [ ] Add lambda operators
- [ ] Add tests
- [ ] Add CI/CD
