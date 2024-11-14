import re
import typing as t
from enum import Enum
from uuid import uuid4


class Operator(str, Enum):
    GTE = "gte"
    GT = "gt"
    LTE = "lte"
    LT = "lt"
    IN = "in"
    STARTSWITH = "startswith"
    ENDSWITH = "endswith"
    CONTAINS = "contains"
    ICONTAINS = "icontains"
    EXACT = "exact"
    IEXACT = "iexact"
    NE = "ne"
    EQ = "eq"


class Rule:
    def __init__(self, *args: "Rule", _id: str | None = None, **conditions: t.Any) -> None:
        self._id = self._validate_id(_id) if _id is not None else str(uuid4())
        self._conditions: t.List[t.Tuple[str, t.Union[dict, "Rule"]]] = []
        for arg in args:
            if isinstance(arg, Rule):
                self._conditions.append(("AND", arg))
            else:
                raise ValueError("positional arguments must be instances of `Rule`")
        if conditions:
            self._conditions.append(("AND", conditions))
        self._negated = False

    @property
    def id(self) -> str:
        return self._id

    def set_id(self, _id: str) -> None:
        """We don't use a @setter because we want this to be very explicit."""
        self._validate_id(_id)
        self._id = _id

    @classmethod
    def _validate_id(cls, _id: str) -> None:
        if not isinstance(_id, str):
            raise ValueError("The ID must be a string")
        if not re.match(r"^[\w-]{1,64}$", _id, re.IGNORECASE):
            raise ValueError(
                "The ID must be <= 64 characters and can only contain letters, numbers, underscores, and hyphens."
            )

    @property
    def conditions(self) -> t.List[t.Tuple[str, t.Union[dict, "Rule"]]]:
        return self._conditions

    @property
    def negated(self) -> bool:
        return self._negated

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
        new_rule._negated = not new_rule.negated
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
        if operator == Operator.GTE:
            return field_value >= condition_value
        elif operator == Operator.GT:
            return field_value > condition_value
        elif operator == Operator.LTE:
            return field_value <= condition_value
        elif operator == Operator.LT:
            return field_value < condition_value
        elif operator == Operator.IN:
            return field_value in condition_value
        elif operator == Operator.STARTSWITH:
            return isinstance(field_value, str) and field_value.startswith(condition_value)
        elif operator == Operator.STARTSWITH:
            return isinstance(field_value, str) and field_value.endswith(condition_value)
        elif operator == Operator.CONTAINS:
            if hasattr(field_value, "__contains__"):
                return condition_value in field_value
        elif operator == Operator.ICONTAINS:
            if isinstance(field_value, str) and isinstance(condition_value, str):
                return condition_value.lower() in field_value.lower()
        elif operator in (Operator.EXACT, Operator.EQ):  # a bit redundant, but it's here for clarity
            return field_value == condition_value
        elif operator == Operator.IEXACT:
            if isinstance(field_value, str) and isinstance(condition_value, str):
                return field_value.lower() == condition_value.lower()
        elif operator == Operator.NE:
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
