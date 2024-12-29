import json
import re
import typing as t
from enum import Enum
from functools import partial
from json import JSONEncoder
from uuid import uuid4


class Operator(str, Enum):
    GTE = "gte"
    GT = "gt"
    LTE = "lte"
    LT = "lt"
    IN = "in"
    IIN = "iin"
    NIN = "nin"
    ININ = "inin"
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
    NOTSET = "notset"
    # FUNC = "func"


AND: t.Literal["AND"] = "AND"
OR: t.Literal["OR"] = "OR"
_OP = t.Literal["AND", "OR"]


class NotSetType:
    def __repr__(self) -> str:  # pragma: no cover
        return "NOT_SET"


NOT_SET = NotSetType()


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


def _iin(field_value: str | None, condition_value: str | list[str]) -> bool:
    if not isinstance(field_value, str):
        raise ValueError("The value for the `IIN` operator must be a string.")
    if isinstance(condition_value, str):
        return field_value.lower() in condition_value.lower()
    if not isinstance(condition_value, t.Iterable):
        raise ValueError("The condition value for the `I[N]IN` operator must be a string or a list of string.")
    if all(isinstance(val, str) for val in condition_value):
        return field_value.lower() in (val.lower() for val in condition_value)
    raise ValueError("The condition value for the `I[N]IN` operator must be a string or a list of string.")


def _inin(field_value: str, condition_value: str | list[str]) -> bool:
    return not _iin(field_value, condition_value)


def _not_set(field_value: t.Any, condition_value: bool) -> bool:
    if field_value is NOT_SET:
        return bool(condition_value)
    return not bool(condition_value)


OPERATOR_FUNCTIONS: t.Dict[str, t.Callable[..., bool]] = {
    Operator.GTE: lambda fv, cv: fv >= cv,
    Operator.GT: lambda fv, cv: fv > cv,
    Operator.LTE: lambda fv, cv: fv <= cv,
    Operator.LT: lambda fv, cv: fv < cv,
    Operator.IN: lambda fv, cv: fv in cv,
    Operator.IIN: _iin,
    Operator.NIN: lambda fv, cv: fv not in cv,
    Operator.ININ: _inin,
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
    Operator.NOTSET: _not_set,
    # Operator.FUNC: _func,
}


class EvaluationResultDict(t.TypedDict):
    field: str | None
    value: t.Any
    operator: str | None
    condition_value: t.Any
    result: bool
    negated: bool
    children: list[tuple[_OP, "EvaluationResultDict"]]


class EvaluationResult:
    def __init__(
        self,
        field: str | None = None,
        value: t.Any = None,
        operator: str | None = None,
        condition_value: t.Any = None,
        result: bool = True,
        negated: bool = False,
    ):
        self.field = field
        self.value = value
        self.operator = operator
        self.condition_value = condition_value
        self.result = result
        self.children: list[tuple[_OP, "EvaluationResult"]] = []
        self.negated = negated

    def __bool__(self) -> bool:
        """Evaluate the result as a boolean, considering negation."""
        if self.children:
            and_combined = all(child[1] for child in self.children if child[0] == AND)
            or_combined = any(child[1] for child in self.children if child[0] == OR)
            res = (self.result and and_combined) or or_combined
            return not res if self.negated else res
        return not self.result if self.negated else self.result

    def __and__(self, other: "EvaluationResult") -> "EvaluationResult":
        if not isinstance(other, EvaluationResult):
            raise ValueError("Operands must be EvaluationResult instances")
        self.children.append((AND, other))
        return self

    def __or__(self, other: "EvaluationResult") -> "EvaluationResult":
        if not isinstance(other, EvaluationResult):
            raise ValueError("Operands must be EvaluationResult instances")
        self.children.append((OR, other))
        return self

    def to_dict(self) -> EvaluationResultDict:
        return EvaluationResultDict(
            field=self.field,
            value=self.value,
            operator=self.operator,
            condition_value=self.condition_value,
            result=self.result,
            negated=self.negated,
            children=[(op, child.to_dict()) for op, child in self.children],
        )

    def to_json(self, *args: t.Any, **kwargs: t.Any) -> str:
        """Serialize the EvaluationResult to a JSON string."""
        kwargs["cls"] = kwargs.get("cls", RuleJSONEncoder)
        return json.dumps(self.to_dict(), *args, **kwargs)

    def __repr__(self) -> str:  # pragma: no cover
        return f"EvaluationResult(result={bool(self)}, children={len(self.children)})"


class Rule:
    def __init__(self, *args: "Rule", **conditions: t.Any) -> None:
        """Create a new Rule instance.

        Args:
            *args: Instances of `Rule` to combine with AND logic.
            **conditions: Conditions to evaluate with the given example data.
                The keys should be field names and the values should be dictionaries
                with operator names as keys and values as values.
                - the special key `__id` can be used to set the rule ID
                - the special key `__raise_on_notset` can be used to raise an exception
                  if a field is not set in the example data and is to be evaluated.
        """
        self._id = self._validate_id(conditions.pop("__id", str(uuid4())))
        self._raise_on_notset = conditions.pop("__raise_on_notset", False)
        self._conditions: list[tuple[_OP, t.Union[dict[str, t.Any], "Rule"]]] = []
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
    def _validate_id(cls, _id: str) -> str:
        if not isinstance(_id, str):
            raise ValueError("The ID must be a string")
        if not re.match(r"^[\w-]{1,64}$", _id, re.IGNORECASE):
            raise ValueError(
                "The ID must be <= 64 characters and can only contain letters, numbers, underscores, and hyphens."
            )
        return _id

    @property
    def conditions(self) -> list[tuple[_OP, t.Union[dict[str, t.Any], "Rule"]]]:
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

    def _evaluate_condition(
        self, condition: t.Union[dict[str, t.Any], "Rule"], example: t.Dict[str, t.Any]
    ) -> EvaluationResult:
        if isinstance(condition, Rule):
            return condition.evaluate(example)

        results = []
        for key, condition_value in condition.items():
            if "__" in key:
                field, operator = key.split("__", 1)
            else:
                field, operator = key, "eq"

            # Evaluate the operator with the example value
            field_value = example.get(field, NOT_SET)
            result = self._evaluate_operator(operator, field_value, condition_value, field)
            results.append(
                EvaluationResult(
                    field=field,
                    value=field_value,
                    operator=operator,
                    condition_value=condition_value,
                    result=result,
                )
            )

        # Combine results using AND logic for all conditions in the dictionary
        combined_result = results[0]
        for res in results[1:]:
            combined_result = combined_result & res
        return combined_result

    def _evaluate_operator(self, operator: str, field_value: t.Any, condition_value: t.Any, field: str) -> bool:
        """Evaluate an operator with the given field and condition values."""
        if field_value is NOT_SET and operator != Operator.NOTSET:
            if self._raise_on_notset:
                raise ValueError(f"Field {field!r} is not set in the example data")
            return False
        if operator in OPERATOR_FUNCTIONS:
            return OPERATOR_FUNCTIONS[operator](field_value, condition_value)
        raise ValueError(f"Unsupported operator: {operator}")

    def evaluate(self, example: t.Dict[str, t.Any]) -> EvaluationResult:
        if not self.conditions:
            return EvaluationResult(result=True)

        combined_result: EvaluationResult | None = None

        for op, condition in self.conditions:
            child_result = self._evaluate_condition(condition, example)
            if combined_result is None:
                combined_result = child_result
            elif op == AND:
                combined_result = combined_result & child_result
            elif op == OR:
                combined_result = combined_result | child_result
            else:  # pragma: no cover
                raise ValueError(f"We should never get here: {op}")

        combined_result.negated = self.negated  # type: ignore[union-attr]
        return t.cast(EvaluationResult, combined_result)

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


def evaluate(rule: Rule, example: t.Dict[str, t.Any]) -> EvaluationResult:
    return rule.evaluate(example)


class RuleJSONEncoder(JSONEncoder):
    """Custom JSON encoder that handles NotSetType."""

    def default(self, obj: t.Any) -> t.Any:
        """Handle NotSetType."""
        if isinstance(obj, NotSetType):
            return None
        return super().default(obj)
