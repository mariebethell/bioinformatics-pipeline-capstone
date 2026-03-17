"""
Shared base structures and helper functions for tool definitions.

Each tool module should expose a TOOL_DEF dictionary with a consistent shape
so the tool registry, validators, and pipeline builder can interact with
every tool the same way.
"""

from typing import Any

def build_tool_def(
        metadata: dict,
        input_contract: dict,
        output_contract: dict,
        arg_schema: dict,
        rules: list | None = None,
        ui_schema: dict | None = None,
        validate_fn = None,
        render_command_fn = None,
        resolve_outputs_fn = None,
) -> dict:
    """
    Builds a normalized tool definition dictionary.
    """
    return {
        "metadata": metadata,
        "input_contract": input_contract,
        "output_contract": output_contract,
        "arg_schema" : arg_schema,
        "rules" : rules or [],
        "ui_schema" : ui_schema or {},
        "validate": validate_fn,
        "render_command": render_command_fn,
        "resolve_outputs": resolve_outputs_fn,
    }

def get_default_args(arg_schema: dict) -> dict:
    """
    Build a dictionary of default argument values from a schema.
    """
    defaults = {}
    for arg_name, spec in arg_schema.items():
        defaults[arg_name] = spec.get("default")
    return defaults

def is_value_of_type(value: Any, expected_type: type) -> bool:
    """
    Runtime type checking helper.
    """
    if expected_type is bool:
        return isinstance(value, bool)
    
    if expected_type is int:
        return isinstance(value, int) and not isinstance(value, bool)
    
    if expected_type is float:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    
    return isinstance(value, expected_type)

def validate_scalar_arg(arg_name: str, value: Any, spec: dict) -> list[str]:
    """
    Validates one scalar argument against its schema definition.

    Returns a list of error strings. Empty list means its valid.
    """
    errors = []

    if value is None:
        if not spec.get("nullable", False):
            errors.append(f"'{arg_name}' cannot be null.")
        return errors
    
    expected_type = spec.get("type")
    if expected_type is not None and not is_value_of_type(value, expected_type):
        errors.append(
            f"'{arg_name}' must be of type {expected_type.__name__}, "
            f"got {type(value).__name__}."
        )
        return errors
    
    allowed_values = spec.get("allowed_values")
    if allowed_values is not None and value not in allowed_values:
        errors.append(
            f"'{arg_name}' must be one of {allowed_values}, got {value!r}."
        )

    min_value = spec.get("min_value")
    if min_value is not None and value < min_value:
        errors.append(f"'{arg_name}' must be >= {min_value}, got {value}.")
    
    max_value = spec.get("max_value")
    if max_value is not None and value > max_value:
        errors.append(f"'{arg_name}' must be <= {max_value}, got {value}.")

    return errors

def validate_args_against_schema(args: dict, schema: dict) -> list[str]:
    """
    Validate a flat argument dictionary against a flat schema dictionary.
    """
    errors = []

    if not isinstance(args, dict):
        return ["Arguments must be a dictionary."]
    
    for arg_name, value in args.items():
        if arg_name not in schema:
            errors.append(f"Unknown argument '{arg_name}'.")
            continue

        errors.extend(validate_scalar_arg(arg_name, value, schema[arg_name]))

    return errors

def apply_defaults(args: dict, schema: dict) -> dict:
    """
    Return a new dictionary where missing keys are filled with schema defaults.
    """
    resolved = {}

    for arg_name, spec in schema.items():
        if arg_name in args:
            resolved[arg_name] = args[arg_name]
        else:
            resolved[arg_name] = spec.get("default")
        
    return resolved