import datetime

from typing import Type

from shared import Command
from shared import Serializer

class CommandFactory:
    """
    Class which handles creation and packaging of the various Command types. All Commands should be instantiated through this class.

    """

    @staticmethod
    def new_command(cmd_type: Type[Command.Command], params=None) -> Command.Command:
        """
        Constructs a Command object of the specified subtype and applies the specified parameters
            - Parameters should line up with the fields specified in the API spec/Command.py
            - Parameters are validated against nullability

        Args:
            cmd_type (Type representing a class which is derived from the Command class): The type of Command to construct
            params (Dictionary): A dictionary containing field : value pairs for each field required by the specified Command type.
                                    You MUST provide values for each non Nullable field. Extra fields will be ignored
                                    Example: For NewPipeline, params could be {"user_uuid": some_uuid, "input_uri": "/some/path", "graph": some_graph}

        Returns:
            A Command of the derived type specified by cmd_type with all the requested fields populated

        Raises:
            TypeError if the given command type is not a derivative of Command
            ValueError if the given parameters are invalid or incomplete for the given command type
        
        """
        
        if not issubclass(cmd_type, Command.Command):
            raise TypeError("Given type is not a Command derivative")

        cmd = cmd_type()
        cmd.timestamp = datetime.datetime.now()

        if params is not None:
            for key, val in params.items():
                setattr(cmd, key, val)

        if (not cmd.validate()):
            raise ValueError("Command failed validation")

        return cmd

    @staticmethod
    def deserialize_command(cmd_type: Type[Command.Command], cmdStr) -> Command.Command:
        """
        Attempts to parse a JSON string and coerce it into the specified type
            - Contains special logic for handing Command subtypes
                - Validates command structure to ensure that they are complete/not malformed
            - Automatically converts serialized Graphs and Nodes into their proper types

        Args:
            obj_type (Type): The type to interpret the JSON string as
            json_string (string): The JSON string to parse

        Returns:
            An object of obj_type containing the data held within the JSON string
                - In some situations the server may return Response instead of the requested obj_type. In those
                    cases, this method will return an object of type Response instead of obj_type!

        Raises:
            TypeError if the fields in the JSON have the incorrect type for the fields within the specified Type
            ValueError if the JSON is missing data which is required by the specified Type

        """
        return Serializer.Serializer.deserialize(cmd_type, cmdStr)

    @staticmethod
    def serialize_command(cmd: Command.Command) -> str:
        """
        Attempts to clone and isolate field data in the given command into a dictionary and serialize the dictionary into a JSON string
            - Automatically converts custom datatypes and enums into more primitive versions which may be serialized
            - Graphs have their Nodes converted into SerializeableNode objects which have no memory references between objects

        Args:
            cmd (Command): The command to clone and serialize into JSON

        Returns:
            A JSON string containing the field data from the given Command

        Raises:
            TypeError if a field in the Command does not match the type specified in the Command's annotations
            ValueError if Command annotation definition is malformed (fix it in Command.py)
            ValueError if timestamp is not an ISO string

        """
        return Serializer.Serializer.serialize_command(cmd)
