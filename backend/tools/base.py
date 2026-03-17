"""
Shared base structures and helper functions for tool definitions.


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
        render_comand_fn = None,
        resolve_outputs_fn = None,
) -> dict:
    
    #Builds a normalized tool definition dictionary.

    return {
        "metadata": metadata,
        "input_contract": input_contract,
        "output_contract": output_contract,
        "arg_schema" : arg_schema,
        "rules" : rules or [],
        "ui_schema" : ui_schema or {},
        "validate": validate_fn,
        "render_comand": render_comand_fn,
        "resolve_outputs": resolve_outputs_fn,
    }