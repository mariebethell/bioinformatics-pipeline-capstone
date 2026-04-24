import asyncio
import ipaddress
import uuid

from network.client.NetClient import NetClient, RequestTypes

from shared.CommandFactory import CommandFactory
from shared.graph import Graph
from shared import Command


class CommandDispatcher:
    """
    Dispatches Commands to the server on behalf of other client layers, abstracting away network IO

    """

    def __init__(self, model, user_uuid: uuid.UUID):
        """
        Constructor for CommandDispatcher
            - Inject dependency for the model into here so it can call it back for graph UI updates
            
        Args:
            model: The model class which should receive the graph UI update data
            user_uuid: The user's UUID. This should never change after installation/should persist between restarts
        
        """

        if user_uuid is None:
            raise TypeError("user_uuid must be given")

        self.user_uuid = user_uuid
        self.net_client = NetClient(self)
        self.model = model

    def connect(self, server_ip: ipaddress.IPv4Address | ipaddress.IPv6Address, server_port: int) -> Command.Response:
        """
        Connects the client to the specified compute server

        Args:
            server_ip (IPv4Address or IPv6Address): IP address for the server to connect to
            server_port (int): Port for the server to connect to

        Returns:
            ClientConnectResponse with server's response. Upon server error, may be of base Response type

        Raises:
            ValueError if given server address/port could not be connected to
            aiohttp.ClientError if server couldn't be reached for some other reason
        
        """

        self.net_client.connect(self.user_uuid, server_ip, server_port)

        params = {
            'user_uuid': self.user_uuid
        }

        cmd = CommandFactory.new_command(Command.ClientConnect, params)
        cmd_str = CommandFactory.serialize_command(cmd)

        resp_dict = asyncio.run(self.net_client.send("/api/client/connect/", RequestTypes.POST, cmd_str))
        resp = CommandFactory.deserialize_command(Command.ClientConnectResponse, resp_dict.get('data', None))

        return resp

    def disconnect(self):
        """
        Disconnects from the compute server's web socket

        Not yet implemented

        """
        raise NotImplementedError #Should just disconnect the websocket

    def new_pipeline(self, graph: Graph, input_data_uri: str) -> Command.Response:
        """
        Requests the server to construct a new pipeline according to the specified graph

        Args:
            graph (Graph): The pipeline specification
            input_data_uri (str): URI to input files on bind mount (this may change? could be redundant info)

        Returns:
            NewPipelineResponse containing the server's response. Upon server error, may be of base Response type

        Raises:
            RuntimeError if not connected to a server
            aiohttp.ClientError if server couldn't be reached

        """

        params = {
            'user_uuid': self.user_uuid,
            'input_uri': input_data_uri,
            'graph': graph
        }

        cmd = CommandFactory.new_command(Command.NewPipeline, params)
        cmd_str = CommandFactory.serialize_command(cmd)

        resp_dict = asyncio.run(self.net_client.send("/api/client/pipeline/new/", RequestTypes.POST, cmd_str))

        resp = CommandFactory.deserialize_command(Command.NewPipelineResponse, resp_dict.get('data', None))
        CommandDispatcher._inject_source(resp, resp_dict.get('source_ip', None))

        return resp


    def overwrite_pipeline(self, graph: Graph, input_data_uri: str) -> Command.Response:
        """
        Requests the server to overwrite a pipeline with a new one according to the specified graph

        Args:
            graph (Graph): The pipeline specification
            input_data_uri (str): URI to input files on bind mount (this may change? could be redundant info)

        Returns:
            OverwritePipelineResponse containing the server's response. Upon server error, may be of base Response type

        Raises:
            RuntimeError if not connected to a server
            aiohttp.ClientError if server couldn't be reached

        """
        params = {
            'user_uuid': self.user_uuid,
            'input_uri': input_data_uri,
            'graph': graph
        }

        cmd = CommandFactory.new_command(Command.OverwritePipeline, params)
        cmd_str = CommandFactory.serialize_command(cmd)

        resp_dict = asyncio.run(self.net_client.send("/api/client/pipeline/overwrite/", RequestTypes.PUT, cmd_str))

        resp = CommandFactory.deserialize_command(Command.OverwritePipelineResponse, resp_dict.get('data', None))
        CommandDispatcher._inject_source(resp, resp_dict.get('source_ip', None))

        return resp

    def get_pipeline(self, pipeline_uuid: uuid.UUID) -> Command.Response:
        """
        Requests the specified pipeline's graph specification from the server

        Args:
            pipeline_uuid (UUID): The UUID for the pipeline you want

        Returns:
            GetPipelineResponse containing the server's response. Upon server error, may be of base Response type

        Raises:
            RuntimeError if not connected to a server
            aiohttp.ClientError if server couldn't be reached

        """
        params = {
            'user_uuid': self.user_uuid,
            'pipeline_id': pipeline_uuid
        }

        cmd = CommandFactory.new_command(Command.GetPipeline, params)
        cmd_str = CommandFactory.serialize_command(cmd)

        resp_dict = asyncio.run(self.net_client.send("/api/client/pipeline/get/", RequestTypes.GET, cmd_str))

        resp = CommandFactory.deserialize_command(Command.GetPipelineResponse, resp_dict.get('data', None))
        CommandDispatcher._inject_source(resp, resp_dict.get('source_ip', None))

        return resp

    def run_pipeline(self, pipeline_uuid: uuid.UUID) -> Command.Response:
        """
        Requests the server to execute an existing pipeline

        Args:
            pipeline_uuid (UUID): The UUID for the pipeline you want to run

        Returns:
            RunPipelineResponse containing the server's response. Upon server error, may be of base Response type

        Raises:
            RuntimeError if not connected to a server
            aiohttp.ClientError if server couldn't be reached

        """

        params = {
            'user_uuid': self.user_uuid,
            'pipeline_id': pipeline_uuid
        }

        cmd = CommandFactory.new_command(Command.RunPipeline, params)
        cmd_str = CommandFactory.serialize_command(cmd)

        resp_dict = asyncio.run(self.net_client.send("/api/client/pipeline/run/", RequestTypes.PATCH, cmd_str))

        resp = CommandFactory.deserialize_command(Command.RunPipelineResponse, resp_dict.get('data', None))
        CommandDispatcher._inject_source(resp, resp_dict.get('source_ip', None))

        return resp

    def stop_pipeline(self, pipeline_uuid: uuid.UUID) -> Command.Response:
        """
        Requests the server to stop running an existing pipeline

        Args:
            pipeline_uuid (UUID): The UUID for the pipeline you want to stop

        Returns:
            StopPipelineResponse containing the server's response. Upon server error, may be of base Response type

        Raises:
            RuntimeError if not connected to a server
            aiohttp.ClientError if server couldn't be reached

        """

        params = {
            'user_uuid': self.user_uuid,
            'pipeline_id': pipeline_uuid
        }

        cmd = CommandFactory.new_command(Command.StopPipeline, params)
        cmd_str = CommandFactory.serialize_command(cmd)

        resp_dict = asyncio.run(self.net_client.send("/api/client/pipeline/stop/", RequestTypes.PATCH, cmd_str))

        resp = CommandFactory.deserialize_command(Command.StopPipelineResponse, resp_dict.get('data', None))
        CommandDispatcher._inject_source(resp, resp_dict.get('source_ip', None))

        return resp

    def revise_stage_params(self, pipeline_uuid: uuid.UUID, stage_num: int, new_args: dict) -> Command.Response:
        """
        Requests the server to update a pipeline stage's arguments/parameters

        Args:
            pipeline_uuid (UUID): The UUID for the pipeline you want to modify
            stage_num (int): The ID for the pipeline node/stage that should be modified
            new_args (dict): Specification for what parameters should be changed to what values. Key is param/arg name, value is the new value

        Returns:
            ModifyPipelineResponse containing the server's response. Upon server error, may be of base Response type

        Raises:
            RuntimeError if not connected to a server
            aiohttp.ClientError if server couldn't be reached

        """

        params = {
            'user_uuid': self.user_uuid,
            'pipeline_id': pipeline_uuid,
            'node_num': stage_num,
            'new_args': new_args
        }

        cmd = CommandFactory.new_command(Command.ModifyPipelineParams, params)
        cmd_str = CommandFactory.serialize_command(cmd)

        resp_dict = asyncio.run(self.net_client.send("/api/client/pipeline/modifyparams/", RequestTypes.PATCH, cmd_str))

        resp = CommandFactory.deserialize_command(Command.ModifyPipelineParamsResponse, resp_dict.get('data', None))
        CommandDispatcher._inject_source(resp, resp_dict.get('source_ip', None))

        return resp

    def rerun_from_stage(self, pipeline_uuid: uuid.UUID, stage_num: int) -> Command.Response:
        """
        Requests the server to restart a pipeline beginning from a specific stage

        Args:
            pipeline_uuid (UUID): The UUID for the pipeline you want to restart
            stage_num (int): The ID for the starting pipeline node/stage for the restart

        Returns:
            RerunPipelineResponse containing the server's response. Upon server error, may be of base Response type

        Raises:
            RuntimeError if not connected to a server
            aiohttp.ClientError if server couldn't be reached

        """

        params = {
            'user_uuid': self.user_uuid,
            'pipeline_id': pipeline_uuid,
            'node_num': stage_num
        }

        cmd = CommandFactory.new_command(Command.RerunStage, params)
        cmd_str = CommandFactory.serialize_command(cmd)

        resp_dict = asyncio.run(self.net_client.send("/api/client/pipeline/rerun/", RequestTypes.PATCH, cmd_str))

        resp = CommandFactory.deserialize_command(Command.RerunStageResponse, resp_dict.get('data', None))
        CommandDispatcher._inject_source(resp, resp_dict.get('source_ip', None))

        return resp

    def rerun_from_start(self, pipeline_uuid: uuid.UUID) -> Command.Response:
        """
        Requests the server to restart a pipeline from the very first stage
            - Same as rerun_from_stage with stage_num set to 0

        Args:
            pipeline_uuid (UUID): The UUID for the pipeline you want to restart

        Returns:
            RerunPipelineResponse containing the server's response. Upon server error, may be of base Response type

        Raises:
            RuntimeError if not connected to a server
            aiohttp.ClientError if server couldn't be reached

        """

        return self.rerun_from_stage(pipeline_uuid, 0)

    def get_result_data_uri(self, pipeline_uuid: uuid.UUID, stage_num: int) -> Command.Response:
        """
        Requests the server to move result files to the bind mount and return their URI so the client may retrieve them

        Args:
            pipeline_uuid (UUID): The UUID for the pipeline which holds the results
            stage_num (int): The ID for the pipeline stage which holds the results you want

        Returns:
            GetArtifactDownloadResponse containing the server's response. Upon server error, may be of base Response type

        Raises:
            RuntimeError if not connected to a server
            aiohttp.ClientError if server couldn't be reached

        """

        params = {
            'user_uuid': self.user_uuid,
            'pipeline_id': pipeline_uuid,
            'node_num': stage_num
        }

        cmd = CommandFactory.new_command(Command.GetArtifactDownload, params)
        cmd_str = CommandFactory.serialize_command(cmd)

        resp_dict = asyncio.run(self.net_client.send("/api/client/pipeline/getdownload/", RequestTypes.GET, cmd_str))

        resp = CommandFactory.deserialize_command(Command.GetArtifactDownloadResponse, resp_dict.get('data', None))
        CommandDispatcher._inject_source(resp, resp_dict.get('source_ip', None))

        return resp

    def handle_async_update(self, payload: str):
        """
        Event handler for incoming socket data. Triggers UI update on server side pipeline stage changes

        Args:
            payload: JSON string received from the server, expected to be a serialized GraphUIUpdate or WebsocketConnectResponse
            
        Raises:
            Nothing, prints errors to console and continues

        """

        cmd = None
        try:
            # 99% of the time it's going to be a GraphUIUpdate
            cmd = CommandFactory.deserialize_command(Command.GraphUIUpdate, payload)
            
        except TypeError | ValueError:
            # It's not a GraphUIUpdate. Only other possibility is that it's a WebsocketConnectResponse
            try:
                cmd = CommandFactory.deserialize_command(Command.WebsocketConnectResponse, payload)
            
            except Exception as e:
                print(f"ERROR: Failed to deserialize incoming websocket message due to: {e}")
                
        if cmd is Command.GraphUIUpdate:
            self.model.update_presented_graph(cmd.UPDATES)
            return
            
        elif cmd is Command.WebsocketConnectResponse:
            return # Don't really need this data right now
            
        print(f"ERROR: CommandDispatcher handle_async_update misconfigured, missing handler for Command type {type(cmd)}")
        return
    
    def trigger_websocket_test(self, pipeline_id: uuid.UUID):
        params = {
            'pipeline_id': pipeline_id
        }

        cmd = CommandFactory.new_command(Command.SendDummyWebsocketUpdate, params)
        cmd_str = CommandFactory.serialize_command(cmd)

        asyncio.run(self.net_client.send("/api/client/debug/websockettest/", RequestTypes.GET, cmd_str))
    
    @staticmethod
    def _inject_source(cmd: Command.Response, source: ipaddress.IPv4Address | ipaddress.IPv6Address):
        """
        Used to inject a Response's source IP into the Response object. Pulls IP from the NIC, not from whatever the source said

        Args:
            cmd (Response): The response to inject IP data into
            source (IPv4Address | IPv6Address): The IP address from the NIC

        Raises:
            Nothing ever. If there's a problem, the Response is left unchanged

        """

        #Try to inject IP back into command, although it isn't important to do so in the client
        try:
            cmd.source = ipaddress.ip_address(source)

        except ValueError | Exception:
            pass # We don't really need it in the client anyway

        return