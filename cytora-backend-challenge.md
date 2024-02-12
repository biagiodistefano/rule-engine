# Cytora - python take home test


## Context


Cytora provides software to insurers to help them manage, classify, and route risks (insurance opportunities). Part of that involves making decisions like:

- Which office or group should handle this risk
- What products are appropriate for this risk
- Whether the risk can be reasonably/profitably insured

One of the main mechanisms we use to do this is a rules engine that operates on
both submitted and inferred data to apply boolean flags (segment tags) to each risk submission.

## Problem

Your task will be to implement a simplified rules engine.

### Final State

We want to be able to express rules like this:

```
Either:
  credit_rating is above 50
  AND
  flood_risk is below 10
OR
  revenue is above 1000000
```

### Requirements

These rules need to be configurable and variable in several ways:
- The number of comparisons
- The variables referenced (e.g. replacing `credit_rating` with something else)
- The constant values being compared against
- The operators being used (e.g. greater than, less than, equals)
- The structure of the boolean composition (i.e where AND/OR/etc are, and where the parentheses are)

### Implementation

We need to be able to apply them to input that looks like this:

```python
EXAMPLE_1 = {
    "credit_rating": 75,
    "flood_risk": 5,
    "revenue": 1000
}
```

In this case, you would produce an output like:

```python
True
```

You need to come up with an appropriate configurable representation for rules like the ones above, express that specific ruleset in your representation, and write a program to apply these rules to various test inputs.
Important: It is up to you how to represent the rules but you DO NOT need to implement any code to turn "text" into such representation!

The whole solution might look like:

```python

EXAMPLE_1 = {...}

RULE = ...

def evaluate(rule, data):
  ...

print(evaluate(RULE, EXAMPLE_1))

```



## Notes
- Use python3
- If you decided to use any dependencies that are not part of the standard library, please explain why.
- If you make any assumptions, call them out explicitly
