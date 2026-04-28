import ipaddress

from rest_framework.request import Request

from network.server.computeServer.gateway.DatagramTools import DatagramTools

class FilterPolicy:
    """
    Base firewall policy class. Used to decide if requests should be blocked or allowed

    """

    def __init__(self):
        self.docker_bridge_range = ipaddress.ip_network('172.17.0.0/16')
    
    def allow_inbound_datagram(self, dg: Request) -> bool:
        """
        Abstract class which makes judgement calls for allowing or rejecting requests
            - Calls abstract method _policy_hook to allow for replacable policy behaviors

        Args:
            dg (rest_framework.request) to be evaluated

        Returns:
            True if allowed, False if the request should be blocked

        """

        try:
            # Reject blatently incorrect datagrams
            if not self._screen_datagram_integrity(dg):
                return False
            
            # Call hook so child classes can inject behavior into this function
            if True in [self._policy_hook(dg), self.enforce_container_origin(dg)]:
                return True
            
            return False
            
        except Exception as e:
            #Default to reject
            print(f"WARNING: Rejecting packet due to unhandled exception: {e}")
            return False
        
    def enforce_container_origin(self, dg: Request) -> bool:
        """
        Used to check if a request originated from a local Docker container
            - Primarily used to ensure that Pipeline update packets are genuine

        Args:
            dg (rest_framework.request) to be evaluated

        Returns:
            True if allowed, False if the request should be blocked

        """

        try:
            ipaddr = DatagramTools.extract_ip(dg)
            return ipaddr in self.docker_bridge_range
            
        except ValueError:
            # Bad IP
            return False
        
    def _policy_hook(self, dg: Request) -> bool:
        """
        Used to allow for interchangable policy behaviors. Called every time a request is being judged
            - Abstract method. Child is expected to implement this.

        Args:
            dg (rest_framework.request) to be evaluated

        Returns:
            True if allowed, False if the request should be blocked

        """

        raise NotImplementedError()
        
    def _screen_datagram_integrity(self, dg: Request) -> bool:
        """
        Screens internal request data for abnormalities
            - Not yet implemented, just allows everything

        Args:
            dg (rest_framework.request) to be evaluated

        Returns:
            True if allowed, False if the request should be blocked
    
        """

        return True #TODO
        raise NotImplementedError()