# Simple Rule engine in pure Python

This rule engine allows for the creation and combination of (nested) rules.

Inspired by the behavior of Django's `Q` object, this rule engine allows for the creation of complex rules that can be evaluated with a dictionary of values.

A `Rule` object is a class that can be initiated wit more `Rule` objects as positional `*args`
and `**kwargs` for additional conditions.

Supported operators are: `gte`, `lte`, `gt`, `lt`, `ne`, `in`, `contains`, `icontains`, `exact`, `iexact`, `startswith`, `endswith`.

More can be added if you are bored enough.

The `Rule` object can be combined with `&` (and), `|` (or).

~~Currently, the `~` (not) operator is not supported but it can be added~~.
I had an after dinner urge to implement it because it was just a few lines of code.

The `Rule` object can be evaluated with a dictionary of values:

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

Of course this is not a full-fledged rule engine, so there is very lacking exception handling and error messages.

Ngl, it was fun to write this. I'm gonna use it for something, I'm sure.