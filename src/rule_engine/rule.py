import json
import re
import typing as t
from enum import Enum
from functools import partial
from uuid import uuid4


class Operator(str, Enum):
    GTE = "gte"
    GT = "gt"
    LTE = "lte"
    LT = "lt"
    IN = "in"
    NIN = "nin"
    STARTSWITH = "startswith"
    ISTARTSWITH = "istartswith"
    ENDSWITH = "endswith"
    IENDSWITH = "iendswith"
    CONTAINS = "contains"
    ICONTAINS = "icontains"
    EXACT = "exact"
    IEXACT = "iexact"
    IS = "is"
    NE = "ne"
    EQ = "eq"
    REGEX = "regex"
    # FUNC = "func"


AND, OR = "AND", "OR"


def _startswith(field_value: t.Any, condition_value: t.Any, case_insensitive: bool = False) -> bool:
    if isinstance(field_value, str) and isinstance(condition_value, str):
        if case_insensitive:
            return field_value.lower().startswith(condition_value.lower())
        return field_value.startswith(condition_value)
    raise ValueError("The value for the `STARTSWITH` operator must be a string.")


def _endswith(field_value: t.Any, condition_value: t.Any, case_insensitive: bool = False) -> bool:
    if isinstance(field_value, str) and isinstance(condition_value, str):
        if case_insensitive:
            return field_value.lower().endswith(condition_value.lower())
        return field_value.endswith(condition_value)
    raise ValueError("The value for the `ENDSWITH` operator must be a string.")


def _contains(field_value: t.Any, condition_value: t.Any, case_insensitive: bool = False) -> bool:
    if isinstance(field_value, str) and isinstance(condition_value, str):
        if case_insensitive:
            return condition_value.lower() in field_value.lower()
    return condition_value in field_value


def _regex(field_value: t.Any, pattern: t.Any) -> bool:
    if isinstance(field_value, str) and isinstance(pattern, (str, re.Pattern)):
        return bool(re.match(pattern, field_value))
    raise ValueError("The value for the `REGEX` operator must be a string or a compiled regex pattern.")


def _func(field_value: t.Any, func: t.Callable[[t.Any], bool]) -> bool:  # pragma: no cover
    if callable(func):
        return func(field_value)
    raise ValueError("The value for the `FUNC` operator must be a callable.")


OPERATOR_FUNCTIONS: t.Dict[str, t.Callable[..., bool]] = {
    Operator.GTE: lambda fv, cv: fv >= cv,
    Operator.GT: lambda fv, cv: fv > cv,
    Operator.LTE: lambda fv, cv: fv <= cv,
    Operator.LT: lambda fv, cv: fv < cv,
    Operator.IN: lambda fv, cv: fv in cv,
    Operator.NIN: lambda fv, cv: fv not in cv,
    Operator.STARTSWITH: partial(_startswith, case_insensitive=False),
    Operator.ISTARTSWITH: partial(_startswith, case_insensitive=True),
    Operator.ENDSWITH: partial(_endswith, case_insensitive=False),
    Operator.IENDSWITH: partial(_endswith, case_insensitive=True),
    Operator.CONTAINS: partial(_contains, case_insensitive=False),
    Operator.ICONTAINS: partial(_contains, case_insensitive=True),
    Operator.EXACT: lambda fv, cv: fv == cv,
    Operator.IS: lambda fv, cv: fv is cv,
    Operator.IEXACT: lambda fv, cv: isinstance(fv, str) and isinstance(cv, str) and fv.lower() == cv.lower(),
    Operator.NE: lambda fv, cv: fv != cv,
    Operator.EQ: lambda fv, cv: fv == cv,
    Operator.REGEX: _regex,
    # Operator.FUNC: _func,
}


class Rule:
    def __init__(self, *args: "Rule", **conditions: t.Any) -> None:
        self._id = str(uuid4())
        self._conditions: t.List[t.Tuple[str, t.Union[dict[str, t.Any], "Rule"]]] = []
        for arg in args:
            if isinstance(arg, Rule):
                self._conditions.append((AND, arg))
            else:
                raise ValueError("positional arguments must be instances of `Rule`")
        if conditions:
            self._conditions.append((AND, conditions))
        self._negated = False

    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, _id: str) -> None:
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
    def conditions(self) -> t.List[t.Tuple[str, t.Union[dict[str, t.Any], "Rule"]]]:
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

    def __invert__(self) -> "Rule":
        new_rule = Rule(self)
        new_rule._negated = not new_rule.negated
        return new_rule

    def _evaluate_condition(self, condition: t.Union[dict[str, t.Any], "Rule"], example: t.Dict[str, t.Any]) -> bool:
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
                        if not self._evaluate_operator("eq", example.get(key, None), value):
                            return False
                return True

        if self.negated:
            return not _eval()
        return _eval()

    @staticmethod
    def _evaluate_operator(operator: str, field_value: t.Any, condition_value: t.Any) -> bool:
        """Evaluate an operator with the given field and condition values."""
        if operator in OPERATOR_FUNCTIONS:
            return OPERATOR_FUNCTIONS[operator](field_value, condition_value)
        raise ValueError(f"Unsupported operator: {operator}")

    def evaluate(self, example: t.Dict[str, t.Any]) -> bool:
        if not self.conditions:
            return True

        result = None
        for op, condition in self.conditions:
            if result is None:
                result = self._evaluate_condition(condition, example)
            elif op == AND:  # type: ignore[unreachable]
                result = result and self._evaluate_condition(condition, example)
            elif op == OR:
                result = result or self._evaluate_condition(condition, example)
            else:  # pragma: no cover
                raise t.assert_never(f"I REALLY should not be here. Unknown operator: {op}")

        return result if result is not None else False

    def to_dict(self) -> dict[str, t.Any]:
        return {
            "$rule": True,
            "id": self.id,
            "negated": self.negated,
            "conditions": [
                {"operator": op, "condition": cond.to_dict() if isinstance(cond, Rule) else cond}
                for op, cond in self.conditions
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> "Rule":
        rule = cls()
        if not data.get("$rule"):
            raise ValueError("Invalid rule data")
        rule._id = data["id"]
        rule._negated = data["negated"]
        for cond in data["conditions"]:
            operator = cond["operator"]
            condition = cond["condition"]
            if isinstance(condition, dict) and condition.get("$rule"):
                condition = cls.from_dict(condition)
            rule.conditions.append((operator, condition))
        return rule

    def to_json(self, *args: t.Any, **kwargs: t.Any) -> str:
        """Serialize the Rule to a JSON string."""
        return json.dumps(self.to_dict(), *args, **kwargs)

    @classmethod
    def from_json(cls, json_str: str) -> "Rule":
        """Deserialize a Rule from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(conditions={self.conditions}, negated={self.negated})"


def evaluate(rule: Rule, example: t.Dict[str, t.Any]) -> bool:
    return rule.evaluate(example)
