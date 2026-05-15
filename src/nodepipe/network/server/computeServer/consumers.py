from channels.generic.websocket import AsyncWebsocketConsumer
import json
from urllib.parse import parse_qs
from uuid import UUID

from shared.CommandFactory import CommandFactory
from shared import Command
from shared.APIStatus import APIStatus

class SocketHandler(AsyncWebsocketConsumer):
    """
    Object which is represents a client's websocket within Django Channels
        - Handles connection, receipt, and disconnection events from the client
        - Defines interface for sending data to the client
        - One instance is spawned per websocket connection, managed by Django Channels

    """

    async def connect(self):
        """
        Overridden method which is automatically called by Django Channels upon receipt of a connection request
            - Opens a channel group for each UUID/user

        """
        
        try:
            # TODO Need to check if IP is valid
            
            client_data = self.scope['client']
            user_ip = client_data[0]
            user_port = client_data[1]
            
            query_params = parse_qs(self.scope['query_string'].decode())
            user_uuid_str = query_params.get('uuid', [None])[0]
            
            if user_uuid_str is None:
                print("ERROR: Websocket connection attempted with no UUID. Rejecting...")
                await self.close() # UUID is required
                
            user_uuid = None
            try: 
                user_uuid = UUID(user_uuid_str)
                user_uuid_str = str(user_uuid) # Normalize formatting
                
            except ValueError:
                print("ERROR: Websocket connection attempted with malformed UUID. Rejecting...")
                await self.close() # Bad UUID

            # At this point user is allowed

            # Make a group for this client (if it doesn't exist already)
            self.user_room = user_uuid_str
            await self.channel_layer.group_add(
                user_uuid_str,
                self.channel_name
            )
            print(f"DBG Websocket room for user UUID {user_uuid_str} with channel name {self.channel_name}")
            
            await self.accept()
        
        except Exception as e:
            
            print(f"Exception while handling websocket connection: {e}")
            params = {"STATUS": APIStatus.ERR_UNKNOWN}
            resp = CommandFactory.new_command(Command.WebsocketConnectResponse, params)
            await self.send_command(resp)
        
    async def receive(self, text_data=None, bytes_data=None):
        """
        Overriden method which handles incoming data from the client
            - This just discards it. We don't need it for this application

        Args:
            text_data: Incoming text data
            bytes_data: Incoming bytes data
        
        """
        print('WARNING: Unexpectedly received data on websocket. Dropping...')
        return # Server doesn't expect to receive data on websocket, only send
        
    async def send_command(self, djangoPayload: dict):
        """
        Method which handles transformation of Commands into strings which are then sent over the websocket

        Args:
            djangoPayload (dict): Dictionary containing Command object at message key
        
        """

        try:
            respStr = CommandFactory.serialize_command(djangoPayload['message'])
            await self.send(text_data=respStr)
            
        except Exception as e:
            print(f"Exception while sending websocket Command: {e}")
            return # Just drop it, node UI updates are not guaranteed anyway
        
    async def disconnect(self, code):
        """
        Overridden method which handles client websocket disconnection. Removes this socket from the message group

        Args:
            code: The error/success reason for disconnection
        
        """

        print('Client disconnected')
        await self.channel_layer.group_discard(self.user_room, self.channel_name)