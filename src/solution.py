from rule_engine import Rule, evaluate

r = Rule(Rule(foo="bar") | Rule(foo="baz"), name="John", age__gte=21) | Rule(name="Jane", age__lt=20)

example_true = {"foo": "bar", "name": "John", "age": 22}
print(evaluate(r, example_true))  # True

example_false = {"name": "Jane", "age": 22}
print(evaluate(r, example_false))  # False

provided_rule = Rule(
    credit_rating__gt=50,
    flood_risk__lt=10,
) | Rule(revenue__gt=1_000_000)

provided_example = {"credit_rating": 75, "flood_risk": 5, "revenue": 1000}

print(evaluate(provided_rule, provided_example))  # True

fancy_complex_rule = (
    Rule(
        Rule(country__in=["USA", "CAN"]) & Rule(revenue__gt=1_000_000),
    )
    | Rule(
        Rule(country__in=["ITA", "FRA", "GER"]) & Rule(revenue__gt=500_000),
    )
) & (Rule(fancy=True) | Rule(complex=True))

fancy_complex_example_true = {"country": "USA", "revenue": 1_000_001, "fancy": True}
print(evaluate(fancy_complex_rule, fancy_complex_example_true))  # True


fancy_complex_example_false = {"country": "ITA", "revenue": 1_000_000, "complex": False}
print(evaluate(fancy_complex_rule, fancy_complex_example_false))  # False


fancy_complex_example_2_true = fancy_complex_example_false = {
    "country": "ITA",
    "revenue": 1_000_000,
    "complex": False,
    "fancy": True,
}
print(evaluate(fancy_complex_rule, fancy_complex_example_2_true))  # True
