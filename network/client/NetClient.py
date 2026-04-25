import ipaddress
import aiohttp
import asyncio
import uuid
import websockets
from threading import Thread, Event
from datetime import datetime, timedelta
from enum import Enum

class RequestTypes(Enum):
    """
    Enumerates the various types of HTTP requests

    """

    GET = 0
    POST = 1
    PUT = 2
    DELETE = 3
    HEAD = 4
    OPTIONS = 5
    PATCH = 6

class NetClient:
    """
    Handles network IO for the client networking layer

    """

    def __init__(self, dispatcher):
        self.server_ip: ipaddress.IPv4Address | ipaddress.IPv6Address
        self.server_port: int
        self.socket_worker = None
        self.socket_worker_kill_sig = Event()
        self.cmd_dispatcher = dispatcher

    def connect(self, user_uuid: uuid.UUID, server_ip: ipaddress.IPv4Address | ipaddress.IPv6Address, server_port: int):
        """
        Attempts to connect to the compute server at the specified IP
            - Pings it first to see if it can reach it
            - Stores IP and port for later use if successful
            - Establishes websocket connection

        Args:
            user_uuid (UUID): Identifier for the user while talking to the compute server. Required for server to talk to us and remember us
                                UUID itself is arbitrary. Just randomly generate it on first startup
            server_ip (IPv4Address or IPv6Address): IP address for the server to connect to
            server_port (int): Port for the server to connect to

        Raises:
            RuntimeError if we are already connected to a websocket
            ValueError if given server address/port could not be connected to
            aiohttp.ClientError if server couldn't be reached for some other reason

        """

        if self.socket_worker is not None:
            raise RuntimeError("Already connected to a websocket!")

        try:
           asyncio.run(NetClient._ping_server(server_ip, server_port))

        except asyncio.TimeoutError | aiohttp.ClientConnectorError | TypeError:
            raise ValueError("Bad server address or port given")

        except aiohttp.ClientError as e:
            print(f"ERROR: Failed to connect to server due to {e}")
            raise e # Rethrow for lower layer to deal with

        self.server_ip = server_ip
        self.server_port = server_port

        self._connect_socket(user_uuid)

    def disconnect(self):
        """
        Raises a signal event to tell the socket worker thread to terminate itself
            - This can take up to one second to finish, but this method will return immediately!

        """
                
        if self.socket_worker is None:
            return
        
        self.socket_worker_kill_sig.set()

    async def send(self, endpoint: str, req_type: RequestTypes, payload: str, mime_type: str = 'application/command') -> dict:
        """
        Sends a Command to the specified endpoint and returns the response

        Args:
            endpoint (str): Network endpoint to hit on the server, such as /api/client/pipeline/new/
            req_type (RequestTypes enum): The type of HTTP request to use, such as GET, POST, PUT etc.
            payload (str): Payload string to send to the server
            mime_type (str): Type of data contained by the payload

        Returns:
            Dictionary containing the servers text response at key 'data' and the IP of whoever responded (hopefully the server???) at 'source_ip'

        Raises:
            RuntimeError if the client is not connected to a server
            TypeError if given an unknown request type
            ValueError if the server returns a status other than 200 OK

        """

        if self.server_ip is None or self.server_port is None:
            raise RuntimeError("Not connected to a server")

        async with aiohttp.ClientSession() as session:
            req_method = session.get
            match req_type:
                case RequestTypes.GET:
                    req_method = session.get

                case RequestTypes.POST:
                    req_method = session.post

                case RequestTypes.PUT:
                    req_method = session.put

                case RequestTypes.DELETE:
                    req_method = session.delete

                case RequestTypes.HEAD:
                    req_method = session.head

                case RequestTypes.OPTIONS:
                    req_method = session.options

                case RequestTypes.PATCH:
                    req_method = session.patch

                case _:
                    raise TypeError("Invalid request type")
                
            headers = {
                'Content-Type': mime_type
            }

            async with req_method(f"http://{self.server_ip}:{self.server_port}{endpoint}", data=payload, headers=headers) as resp:
                if resp.status != 200:
                    raise ValueError("Server returned bad status")
                
                data_str = await resp.json() #aiohttp wraps our json from the server in a second json
                return {'data': data_str, 'source_ip': resp.host}

    def _connect_socket(self, user_uuid: uuid.UUID):
        """
        Establishes websocket connection with server for client UI updates (such as on stage completion)

        Args:
            user_uuid: UUID which represents this user's identity to the server
                        Should never change even between client restarts

        Raises:
            RuntimeError if the client is not connected to a server

        """

        if self.server_ip is None or self.server_port is None:
            raise RuntimeError("Not connected to a server")  
            
        def worker_task():
            asyncio.run(self._socket_worker(user_uuid))

        self.socket_worker = Thread(target=worker_task, daemon=True)
        self.socket_worker.start()
        
        
    async def _socket_worker(self, uuid: uuid.UUID):
        """
        Worker function which handles the websocket connection with the server
            Should be called as a task or this will stall the program

        Args:
            user_uuid: UUID which represents this user's identity to the server
                        Should never change even between client restarts
        
        """

        url = f"ws://{self.server_ip}:{self.server_port}/api/client/connect?uuid={str(uuid)}"
        print(url)
        async with websockets.connect(url) as websocket:
            print("INFO: Socket connected to server")
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    print(f"INFO: Received message on websocket: {message}")
                    self.cmd_dispatcher.handle_async_update(message)

                except websockets.ConnectionClosedOK:
                    print("INFO: Websocket connection closed")
                    return

                except websockets.ConnectionClosedError as e:
                    print(f"ERROR: Websocket connection closed due to error: {e}")
                    return
                
                except asyncio.TimeoutError:
                    # Check if thread should be stopped
                    if self.socket_worker_kill_sig.is_set():
                        self.socket_worker_kill_sig.clear()
                        self.socket_worker = None
                        return

                except Exception as e:
                    print(f"ERROR: Exception during receipt of websocket message: {e}\n\n Continuing...")
                    

    @staticmethod
    async def _ping_server(server_ip: ipaddress.IPv4Address | ipaddress.IPv6Address, server_port: int) -> timedelta:
        """
        Sends a ping request to the server and times the round trip time

        Args:
            server_ip (IPv4Address or IPv6Address): IP address for the server to ping
            server_port (int): Port for the server to ping
        
        Returns:
            timedelta containing the round trip time

        Raises:
            TypeError if server ip or port is None
            asyncio.TimeoutError if connection times out
            aiohttp.ClientConnectorError if connection could not be established
            ValueError if the server responded but gave a status other than 200 OK

        """

        if server_ip is None or server_port is None:
            raise TypeError("You must supply a server to ping")

        starting_time = datetime.now()
        async with aiohttp.ClientSession() as session:
            req_method = session.get

            async with req_method(f"http://{server_ip}:{server_port}/api/ping/") as resp:
                if resp.status != 200:
                    raise ValueError("Server returned bad status")
                
                midway_time = await resp.json()
                ending_time = datetime.now()
                
                return ending_time - starting_time