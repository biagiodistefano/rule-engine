# utils.py

import re
import typing as t

# Assuming rule.py is in the same package or accessible
from .rule import _OP, AND, OR, Operator, Rule

# Define JSONSchema type alias
JSONSchema = t.Dict[str, t.Any]

# --- Type Definitions ---
ConditionValue = t.Any
FieldName = str
OperatorStr = str
ConditionDict = t.Dict[str, ConditionValue]
RuleOrCondition = t.Union[Rule, ConditionDict]
ConditionTuple = t.Tuple[_OP, RuleOrCondition]

# --- Helper Functions ---


def _is_numeric(value: t.Any) -> bool:
    """Check if value is int or float, but not bool."""
    # isinstance(True, int) is True, so we need to exclude bool explicitly
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# --- Operator to JSON Schema Mapping ---
# Functions generating the core constraint part of the schema


def _schema_gte(value: ConditionValue) -> JSONSchema:
    if not _is_numeric(value):
        raise TypeError(f"Operator 'gte' requires a numeric value (int/float), got {type(value).__name__}")
    return {"type": "number", "minimum": value}


def _schema_gt(value: ConditionValue) -> JSONSchema:
    if not _is_numeric(value):
        raise TypeError(f"Operator 'gt' requires a numeric value (int/float), got {type(value).__name__}")
    return {"type": "number", "exclusiveMinimum": value}


def _schema_lte(value: ConditionValue) -> JSONSchema:
    if not _is_numeric(value):
        raise TypeError(f"Operator 'lte' requires a numeric value (int/float), got {type(value).__name__}")
    return {"type": "number", "maximum": value}


def _schema_lt(value: ConditionValue) -> JSONSchema:
    if not _is_numeric(value):
        raise TypeError(f"Operator 'lt' requires a numeric value (int/float), got {type(value).__name__}")
    return {"type": "number", "exclusiveMaximum": value}


def _schema_in(value: ConditionValue) -> JSONSchema:
    # Note: The library's 'iin' handles string contains, but JSON Schema 'enum' needs a list.
    # We stick to the list requirement here for both 'in' and 'iin'.
    if not isinstance(value, (list, tuple, set)):
        raise TypeError(
            f"Operator 'in'/'iin' requires a list/tuple/set value for schema generation, got {type(value).__name__}"
        )

    # Use list(value) in case it's a set/tuple
    value_list = list(value)
    inferred_type = None
    if value_list:
        first_item = value_list[0]
        # Determine type based on first item (best effort)
        if isinstance(first_item, str):
            inferred_type = "string"
        elif isinstance(first_item, bool):
            inferred_type = "boolean"  # Check before int
        elif isinstance(first_item, int):
            inferred_type = "integer"
        elif isinstance(first_item, float):
            inferred_type = "number"
        elif isinstance(first_item, list):
            inferred_type = "array"
        elif isinstance(first_item, dict):  # pragma: no branch
            inferred_type = "object"
        # Note: null type inference is tricky with enum

    schema: JSONSchema = {"enum": value_list}
    if inferred_type:
        schema["type"] = inferred_type
    return schema


def _schema_nin(value: ConditionValue) -> JSONSchema:
    # Relies on _schema_in's type check
    enum_schema = _schema_in(value)
    return {"not": enum_schema}


def _schema_startswith(value: ConditionValue) -> JSONSchema:
    # Handles 'startswith' and 'istartswith' (approximated)
    if not isinstance(value, str):
        raise TypeError(f"Operator 'startswith'/'istartswith' requires a string value, got {type(value).__name__}")
    return {"type": "string", "pattern": f"^{re.escape(value)}"}


def _schema_endswith(value: ConditionValue) -> JSONSchema:
    # Handles 'endswith' and 'iendswith' (approximated)
    if not isinstance(value, str):
        raise TypeError(f"Operator 'endswith'/'iendswith' requires a string value, got {type(value).__name__}")
    return {"type": "string", "pattern": f"{re.escape(value)}$"}


def _schema_contains(value: ConditionValue) -> JSONSchema:
    # Handles 'contains' and 'icontains' (approximated for strings only)
    if not isinstance(value, str):
        raise TypeError(
            f"Operator 'contains'/'icontains' (schema generation) requires a string value, got {type(value).__name__}"
        )
    # JSON Schema pattern matches anywhere
    return {"type": "string", "pattern": re.escape(value)}


def _schema_exact(value: ConditionValue) -> JSONSchema:
    # Handles 'exact', 'eq', 'is', 'iexact' (approximated)
    schema: JSONSchema = {"const": value}
    # Add type based on value for better validation
    if isinstance(value, str):
        schema["type"] = "string"
    elif isinstance(value, bool):
        schema["type"] = "boolean"  # Check before int
    elif isinstance(value, int):
        schema["type"] = "integer"
    elif isinstance(value, float):
        schema["type"] = "number"
    elif value is None:
        schema["type"] = "null"
    elif isinstance(value, list):
        schema["type"] = "array"
    elif isinstance(value, dict):  # pragma: no branch
        schema["type"] = "object"
    return schema


def _schema_ne(value: ConditionValue) -> JSONSchema:
    # Handles 'ne'
    const_schema = _schema_exact(value)
    return {"not": const_schema}


def _schema_regex(value: ConditionValue) -> JSONSchema:
    # Handles 'regex'
    if not isinstance(value, (str, re.Pattern)):
        raise TypeError(f"Operator 'regex' requires a string or regex pattern value, got {type(value).__name__}")
    pattern = value if isinstance(value, str) else value.pattern
    return {"type": "string", "pattern": pattern}


# --- Operator Mapping (Updated) ---

_OPERATOR_SCHEMA_GENERATORS: t.Dict[Operator, t.Callable[[ConditionValue], JSONSchema]] = {
    # Standard Operators
    Operator.GTE: _schema_gte,
    Operator.GT: _schema_gt,
    Operator.LTE: _schema_lte,
    Operator.LT: _schema_lt,
    Operator.IN: _schema_in,
    Operator.NIN: _schema_nin,
    Operator.STARTSWITH: _schema_startswith,
    Operator.ENDSWITH: _schema_endswith,
    Operator.CONTAINS: _schema_contains,  # String contains only
    Operator.EXACT: _schema_exact,
    Operator.EQ: _schema_exact,  # Treat eq as exact
    Operator.NE: _schema_ne,
    Operator.REGEX: _schema_regex,
    Operator.IS: _schema_exact,  # Approximate 'is' with 'const'
    Operator.NOTSET: lambda v: {},  # Handled structurally
    # Case-insensitive Operators (Mapped to case-sensitive approximations)
    Operator.IIN: _schema_in,  # Approximated by 'in' (requires list value)
    Operator.ININ: _schema_nin,  # Approximated by 'nin' (requires list value)
    Operator.ISTARTSWITH: _schema_startswith,  # Approximated by 'startswith'
    Operator.IENDSWITH: _schema_endswith,  # Approximated by 'endswith'
    Operator.ICONTAINS: _schema_contains,  # Approximated by 'contains' (string only)
    Operator.IEXACT: _schema_exact,  # Approximated by 'exact'/'const'
}

# --- Schema Merging and Translation Logic (Minor adjustments needed) ---


def _get_operator_enum(op_str: OperatorStr) -> Operator:
    """Gets the Operator enum member from a string."""
    try:
        return Operator(op_str)
    except ValueError:
        raise ValueError(f"Unsupported operator string: {op_str}") from None


def _merge_schemas_and(schemas: t.List[JSONSchema]) -> JSONSchema:
    """Merges multiple schemas using 'allOf'. Filters out empty schemas."""
    valid_schemas = [s for s in schemas if s]  # Filter out {} which means "match anything"
    if not valid_schemas:
        return {}  # AND of nothing or only {} is {}
    if len(valid_schemas) == 1:
        return valid_schemas[0]
    # Flatten nested allOf
    flat_schemas = []
    for s in valid_schemas:
        # Check if it's a dict and has 'allOf' key which is a list
        if isinstance(s, dict) and isinstance(s.get("allOf"), list):
            flat_schemas.extend(s["allOf"])
        else:
            flat_schemas.append(s)
    # Deduplicate? Maybe not necessary, JSON Schema allows redundant clauses.
    return {"allOf": flat_schemas}


def _merge_schemas_or(schemas: t.List[JSONSchema]) -> JSONSchema:
    """Merges multiple schemas using 'anyOf'. Handles special cases."""
    # OR with "match nothing" ({'not': {}}) can be ignored if other options exist
    valid_schemas = [s for s in schemas if s != {"not": {}}]
    if not valid_schemas:
        # If only "match nothing" schemas were present, the result is "match nothing"
        return {"not": {}} if schemas else {"not": {}}  # OR of nothing is false

    # OR with "match anything" ({}) makes the whole result "match anything"
    if any(s == {} for s in valid_schemas):
        return {}  # Match anything

    if len(valid_schemas) == 1:
        return valid_schemas[0]

    # Flatten nested anyOf
    flat_schemas = []
    for s in valid_schemas:
        # Check if it's a dict and has 'anyOf' key which is a list
        if isinstance(s, dict) and isinstance(s.get("anyOf"), list):
            flat_schemas.extend(s["anyOf"])
        else:
            flat_schemas.append(s)
    # Deduplicate? Optional.
    return {"anyOf": flat_schemas}


def _translate_single_condition(field: FieldName, operator: Operator, value: ConditionValue) -> JSONSchema:
    """
    Translates a single 'field__operator=value' condition into a JSON schema fragment.
    """
    if operator == Operator.NOTSET:
        if value is True:
            return {"not": {"required": [field]}}
        elif value is False:
            return {"required": [field]}
        else:
            raise ValueError(f"Operator 'notset' requires a boolean value, got {type(value).__name__}")

    if operator not in _OPERATOR_SCHEMA_GENERATORS:
        # Should not happen with the updated mapping, but good safeguard
        raise NotImplementedError(
            f"Schema generation mapping missing for operator: {operator.value}"
        )  # pragma: no cover

    constraint_schema_gen = _OPERATOR_SCHEMA_GENERATORS[operator]
    try:
        # Generate the constraint part (e.g., {"minimum": 5}, {"enum": [...]})
        constraint_schema = constraint_schema_gen(value)
    except (TypeError, ValueError) as e:  # Catch expected errors from generators
        # Add context for better debugging
        raise type(e)(f"Error processing condition for field '{field}': {e}") from e
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            f"Unexpected error generating schema constraint for field '{field}' with operator '{operator.value}': {e}"
        ) from e

    # Combine constraint with field structure and requirement.
    # If constraint_schema is empty (e.g., from NOTSET lambda, handled above), don't create properties.
    # But for other operators, even if the constraint itself is simple like {"type": "string"},
    # we embed it within the properties structure.
    return {
        "type": "object",  # Assume parent is an object
        "properties": {field: constraint_schema},
        "required": [field],  # Field must exist for the condition to apply (except for notset=True)
    }


def _dict_conditions_to_schema(condition_dict: ConditionDict) -> JSONSchema:
    """
    Converts a dictionary of conditions (implicitly ANDed) into a JSON schema.
    """
    schemas_to_and: t.List[JSONSchema] = []
    for key, value in condition_dict.items():
        if "__" in key:
            field, op_str = key.split("__", 1)
        else:
            field, op_str = key, Operator.EQ.value  # Default operator is EQ

        try:
            operator = _get_operator_enum(op_str)
            # Translate this single condition
            schema = _translate_single_condition(field, operator, value)
            schemas_to_and.append(schema)
        # Propagate specific errors clearly
        except (ValueError, TypeError, NotImplementedError) as e:
            raise e
        except Exception as e:  # pragma: no cover
            raise RuntimeError(f"Unexpected error translating condition '{key}={value}': {e}") from e

    # Merge all conditions from the dict using AND logic
    return _merge_schemas_and(schemas_to_and)


# --- Main Conversion Function ---


def rule_to_schema(rule: Rule) -> JSONSchema:
    """
    Converts a Rule object into a JSON Schema.
    ...(docstring)...
    """
    # --- Calculate base_schema based on conditions (propagation adjustment) ---
    if not rule.conditions:
        base_schema: JSONSchema = {}  # Match anything
    else:
        or_groups: t.List[JSONSchema] = []
        current_and_group: t.List[JSONSchema] = []

        for i, (op, condition) in enumerate(rule.conditions):
            sub_schema: JSONSchema
            try:
                if isinstance(condition, Rule):
                    sub_schema = rule_to_schema(condition)  # Recursive call
                elif isinstance(condition, dict):
                    sub_schema = _dict_conditions_to_schema(condition)
                else:
                    # Should not happen based on Rule implementation
                    raise TypeError(f"Unexpected condition type: {type(condition).__name__}")  # pragma: no cover
            except (NotImplementedError, TypeError, ValueError) as e:
                # Catch errors during sub-schema generation and propagate
                # Add context about which part of the rule failed? Maybe too verbose.
                raise e  # Re-raise the specific error
            except Exception as e:  # pragma: no cover
                raise RuntimeError(f"Unexpected error processing rule condition {i}: {condition}") from e

            # Grouping logic (remains the same)
            if i == 0:
                current_and_group.append(sub_schema)
            elif op == AND:
                current_and_group.append(sub_schema)
            elif op == OR:
                if current_and_group:  # pragma: no branch
                    or_groups.append(_merge_schemas_and(current_and_group))
                current_and_group = [sub_schema]
            else:  # pragma: no cover
                raise ValueError(f"Unexpected operator between conditions: {op}")

        if current_and_group:  # pragma: no branch
            or_groups.append(_merge_schemas_and(current_and_group))

        base_schema = _merge_schemas_or(or_groups)
    # --- End base_schema calculation ---

    # --- Apply negation (Corrected Logic) ---
    if rule.negated:
        # Check for existing 'not' ONLY if base_schema IS a dict AND has 'not' as its ONLY key
        # This handles double negation simplification: not(not(X)) -> X
        if isinstance(base_schema, dict) and list(base_schema.keys()) == ["not"]:
            # Double negation: return the inner schema
            return base_schema["not"]  # type: ignore[no-any-return]
        else:
            # Apply standard negation for all other cases, including base_schema = {}
            # If base_schema is {}, result is {"not": {}} -> Matches nothing
            # If base_schema is non-empty, result is {"not": base_schema}
            return {"not": base_schema}
    else:
        # Not negated, return the calculated base schema
        return base_schema
