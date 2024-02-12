import typing as t


class Rule:
    def __init__(self, *args: "Rule", **conditions: t.Any) -> None:
        self.conditions: t.List[t.Tuple[str, t.Union[dict, "Rule"]]] = []
        for arg in args:
            if isinstance(arg, Rule):
                self.conditions.append(("AND", arg))
            else:
                raise ValueError("positional arguments must be instances of `Rule`")
        if conditions:
            self.conditions.append(("AND", conditions))
        self.negated = False

    def __and__(self, other: "Rule") -> "Rule":
        if not isinstance(other, Rule):
            raise ValueError("The right operand must be an instance of `Rule`")
        return Rule(self, other)

    def __or__(self, other: "Rule") -> "Rule":
        if not isinstance(other, Rule):
            raise ValueError("The right operand must be an instance of `Rule`")
        new_rule = Rule(self)
        new_rule.conditions.append(("OR", other))
        return new_rule

    def __invert__(self):
        new_rule = Rule(self)
        new_rule.negated = not new_rule.negated
        return new_rule

    def _evaluate_condition(self, condition: t.Union[dict, "Rule"], example: t.Dict[str, t.Any]) -> bool:
        def _eval() -> bool:
            if isinstance(condition, Rule):
                return condition.evaluate(example)
            else:
                for key, value in condition.items():
                    if "__" in key:
                        field, op = key.split("__", 1)
                        if not self._evaluate_operator(op, example.get(field, None), value):
                            return False
                    else:
                        if key not in example or example[key] != value:
                            return False
                return True

        if self.negated:
            return not _eval()
        return _eval()

    @staticmethod
    def _evaluate_operator(operator: str, field_value: t.Any, condition_value: t.Any) -> bool:
        if operator == "gte":
            return field_value >= condition_value
        elif operator == "gt":
            return field_value > condition_value
        elif operator == "lte":
            return field_value <= condition_value
        elif operator == "lt":
            return field_value < condition_value
        elif operator == "in":
            return field_value in condition_value
        elif operator == "startswith":
            return isinstance(field_value, str) and field_value.startswith(condition_value)
        elif operator == "endswith":
            return isinstance(field_value, str) and field_value.endswith(condition_value)
        elif operator == "contains":
            if isinstance(condition_value, str):
                return condition_value in field_value
            else:
                return field_value in condition_value
        elif operator == "icontains":
            if isinstance(field_value, str) and isinstance(condition_value, str):
                return condition_value.lower() in field_value.lower()
        elif operator == "exact":  # a bit redundant, but it's here for clarity
            return field_value == condition_value
        elif operator == "iexact":
            if isinstance(field_value, str) and isinstance(condition_value, str):
                return field_value.lower() == condition_value.lower()
        elif operator == "ne":
            return field_value != condition_value
        return False

    def evaluate(self, example: t.Dict[str, t.Any]) -> bool:
        if not self.conditions:
            return True

        result = None
        for op, condition in self.conditions:
            if result is None:
                result = self._evaluate_condition(condition, example)
            elif op == "AND":
                result = result and self._evaluate_condition(condition, example)
            elif op == "OR":
                result = result or self._evaluate_condition(condition, example)
            else:
                raise ValueError(f"I REALLY should not be here. Unknown operator: {op}")

        return result if result is not None else False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(conditions={self.conditions}, negated={self.negated})"


def evaluate(rule: Rule, example: t.Dict[str, t.Any]) -> bool:
    return rule.evaluate(example)
