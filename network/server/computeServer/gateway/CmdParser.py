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
        Called by Django to automatically parse incoming JSON strings into Commands

        Args:
            stream: Stream containing Command JSON data
            media_type: MIME type for incoming data. Should always be application/command or the JSON will be rejected
            parser_context (dict): Contains data which may be useful for the parser. In this case, we configured Django
                                    to put the command subtype in there so we know what exactly to deserialize into
        Returns:
            A Command containing all the information given in the JSON string and of the type specified in the parser_context

        Raises:
            TypeError if the MIME type is incorrect
            TypeError if parser_context is requesting to deserialize into an object which is not a Command or Command derivative
            ValueError if no parser_context is given

        """

        if media_type != CommandParser.media_type:
            raise TypeError("Media type mismatch")
        
        if parser_context is None:
            raise ValueError("parser_context is required")

        cmd_type = parser_context.get('cmd_type', None)
        if cmd_type is None or not issubclass(cmd_type, Command.Command):
            raise TypeError("Given type is not a Command derivative")
        
        cmd_json = stream.read()
        
        cmd = CommandFactory.CommandFactory.deserialize_command(cmd_type, cmd_json)

        return cmd