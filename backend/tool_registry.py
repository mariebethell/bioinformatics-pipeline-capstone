from backend.tools.base import get_default_args
from backend.tools.fastqc import fastqc_tool
from backend.tools.trimmomatic import trimmomatic_tool
from backend.tools.trinity import trinity_tool


class ToolRegistry:
    """
    Central registry for backend tool definitions.

    This module is the bridge between graph nodes and tool schema modules.

    Responsibilities are storing the cannonical mapping of tool keys -> tool_dif dictionaries.
    normalizing tool names coming from the UI/graph layer. Exposing helper functions for validation,
    defaults, output resolution and command rendering.
    """

    def __init__(self):
        # cannonical registry: backend key -> tool definition
        self.tool_registry = {
            "fastqc": fastqc_tool,
            "trimmomatic": trimmomatic_tool,
            "trinity": trinity_tool 
        }

        self.tool_aliases = {
            "fastqc": "fastqc",
            "FastQC": "fastqc",
            "trimmomatic": "trimmomatic",
            "Trimmomatic": "trimmomatic",
            "Trinity": "trinity",
            "De Novo Transcriptome Assembly": "trinity",
        }

    def normalize_tool_key(self, tool_name: str) -> str:
        """
        Convert a tool name or alias into the canonical registry key.

        Example:
            "FastQC" -> "fastqc"
            "Trimmomatic" -> "trimmomatic"
        """
        if not isinstance(tool_name, str) or not tool_name.strip():
            raise ValueError("Tool name must be a non-empty string.")

        if tool_name in self.tool_aliases:
            return self.tool_aliases[tool_name]

        lowered = tool_name.strip().lower()
        if lowered in self.tool_aliases:
            return self.tool_aliases[lowered]

        raise KeyError(f"Unknown tool '{tool_name}'.")

    def get_tool_def(self, tool_name: str) -> dict:
        """
        Return the full tool definition dictionary for a tool.
        """
        canonical_key = self.normalize_tool_key(tool_name)
        return self.tool_registry[canonical_key]

    def is_registered_tool(self, tool_name: str) -> bool:
        """
        Return True if the given tool name or alias is recognized.
        """
        try:
            self.normalize_tool_key(tool_name)
            return True
        except (KeyError, ValueError):
            return False

    def list_registered_tools(self) -> list[str]:
        """
        Return canonical tool keys currently registered.
        """
        return list(self.tool_registry.keys())

    def get_tool_metadata(self, tool_name: str) -> dict:
        """
        Return metadata for a registered tool.
        """
        return self.get_tool_def(tool_name)["metadata"]

    def get_tool_input_contract(self, tool_name: str) -> dict:
        """
        Return input contract for a registered tool.
        """
        return self.get_tool_def(tool_name)["input_contract"]

    def get_tool_output_contract(self, tool_name: str) -> dict:
        """
        Return output contract for a registered tool.
        """
        return self.get_tool_def(tool_name)["output_contract"]

    def get_tool_arg_schema(self, tool_name: str) -> dict:
        """
        Return flat arg schema for a registered tool.
        """
        return self.get_tool_def(tool_name)["arg_schema"]

    def get_tool_ui_schema(self, tool_name: str) -> dict:
        """
        Return UI schema for a registered tool.
        """
        return self.get_tool_def(tool_name)["ui_schema"]

    def get_tool_rules(self, tool_name: str) -> list:
        """
        Return any rule strings attached to the tool definition.
        """
        return self.get_tool_def(tool_name)["rules"]

    def get_default_tool_args(self, tool_name: str) -> dict:
        """
        Build default arguments from a tool's flat arg schema.

        Note:
        This only fills defaults for flat schema keys.
        Structured fields like Trimmomatic 'steps' must still be
        handled separately by the caller.
        """
        tool_def = self.get_tool_def(tool_name)
        return get_default_args(tool_def["arg_schema"])

    def validate_tool_args(self, tool_name: str, args: dict, context: dict | None = None) -> list[str]:
        """
        Validate node args using the tool's custom validator.
        """
        tool_def = self.get_tool_def(tool_name)
        validate_fn = tool_def.get("validate")

        if validate_fn is None:
            return []

        return validate_fn(args, context=context)

    def resolve_tool_outputs(self, tool_name: str, node_args: dict, context: dict) -> dict:
        """
        Resolve backend-managed outputs for a node.
        """
        tool_def = self.get_tool_def(tool_name)
        resolve_fn = tool_def.get("resolve_outputs")

        if resolve_fn is None:
            return {}

        return resolve_fn(node_args, context)

    def render_tool_command(
        self,
        tool_name: str,
        node_args: dict,
        resolved_inputs: dict,
        resolved_outputs: dict,
    ) -> list[str]:
        """
        Render a command for a tool as a list of CLI parts.
        """
        tool_def = self.get_tool_def(tool_name)
        render_fn = tool_def.get("render_command")

        if render_fn is None:
            raise ValueError(f"Tool '{tool_name}' does not define render_command().")

        return render_fn(node_args, resolved_inputs, resolved_outputs)

    def can_tool_accept_input(self, tool_name: str, input_format: str) -> bool:
        """
        Check whether a tool declares support for a given input format.
        """
        input_contract = self.get_tool_input_contract(tool_name)
        accepted_formats = input_contract.get("accepted_formats", [])
        return input_format in accepted_formats