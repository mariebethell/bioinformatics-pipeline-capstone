from channels.generic.websocket import AsyncWebsocketConsumer
import json
from urllib.parse import parse_qs
import uuid

from shared.CommandFactory import CommandFactory
from shared import Command
from shared.APIStatus import APIStatus

class SocketHandler(AsyncWebsocketConsumer):
    async def connect(self):
        
        try:
            # Need to check if already connected elsewhere but for now just accept for testing
            
            client_data = self.scope['client']
            user_ip = client_data[0]
            user_port = client_data[1]
            
            query_params = parse_qs(self.scope['query_string'].decode())
            user_uuid_str = query_params.get('uuid', [None])[0]
            
            if user_uuid is None:
                print("ERROR: Websocket connection attempted with no UUID. Rejecting...")
                await self.close() # UUID is required
                
            user_uuid = None
            try: 
                user_uuid = uuid(user_uuid_str)
                
            except ValueError:
                print("ERROR: Websocket connection attempted with malformed UUID. Rejecting...")
                await self.close() # Bad UUID

            # At this point user is allowed

            # Make a group for this client (if it doesnt exist already)
            self.user_room = user_uuid_str
            await self.channel_layer.group_add(
                self.user_room,
                self.channel_name
            )
            
            
            await self.accept()
            
            params = {"STATUS": APIStatus.SUCCESS}
            resp = CommandFactory.new_command(Command.WebsocketConnectResponse, params)
            self.sendCommand(resp)
        
        except Exception as e:
            
            print(f"Exception while handling websocket connection: {e}")
            params = {"STATUS": APIStatus.ERR_UNKNOWN}
            resp = CommandFactory.new_command(Command.WebsocketConnectResponse, params)
            self.sendCommand(resp)
        
    async def receive(self, text_data):
        print('WARNING: Unexpectedly received data on websocket. Dropping...')
        return # Server doesn't expect to receive data on websocket, only send
        
    async def send_command(self, command: Command):
        try:
            respStr = CommandFactory.serialize_command(command)
            await.self.send(text_data=respStr)
            
        except Exception as e:
            print(f"Exception while sending websocket Command: {e}")
            return # Just drop it, node UI updates are not guaranteed anyway
        
    async def disconnect(self, close_code):
        print('Client disconnected')
        await self.channel_layer.group_discard(self.group_name, self.channel_name)