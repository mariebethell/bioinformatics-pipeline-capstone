from rest_framework.parsers import BaseParser

from shared import CommandFactory
from shared import Command

class CommandParser(BaseParser):
    """
    Parses JSON into Command objects using the CommandFactory

    """
    media_type = 'application/command'

    def parse(self, stream, media_type: str = None, parser_context: dict = None) -> Command.Command:
        """
        Asks the CommandFactory to construct the Command for us

        """

        if media_type != CommandParser.media_type:
            raise TypeError("Media type mismatch")
        
        if parser_context is None:
            raise TypeError("parser_context is required")

        cmd_type = parser_context.get('cmd_type', None)
        if cmd_type is None or not issubclass(cmd_type, Command.Command):
            raise TypeError("Given type is not a Command derivative")
        
        cmd_json = stream.read()
        
        cmd = CommandFactory.CommandFactory.deserialize_command(cmd_type, cmd_json)

        return cmd