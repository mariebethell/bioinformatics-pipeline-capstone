from rest_framework.request import Request
import socket
import ipaddress

from network.server.computeServer.gateway import FilterPolicy
from network.server.computeServer.gateway.DatagramTools import DatagramTools

class LocalPolicy(FilterPolicy.FilterPolicy):
    """
    Used to define firewall behavior when server is deployed on the local machine
        - Rejects any Commands from remote IPs

    """

    # Override parent hook
    def _policy_hook(self, dg: Request) -> bool:
        """
        Called by base class while evaluating firewall policy to allow for specialized behaviors
            - In this case, calls _source_is_local_machine to block remote requests

        Args:
            dg (rest_framework.request) to be evaluated

        Returns:
            True if allowed, False if the request should be blocked

        """
        return self._source_is_local_machine(dg)
        
    def _source_is_local_machine(self, dg: Request) -> bool:
        """
        Rejects any requests which originate from remote IP addresses

        Args:
            dg (rest_framework.request) to be evaluated

        Returns:
            True if allowed, False if the request should be blocked

        Raises:
            ValueError if source IP in request is invalid

        """

        ipaddr = None
        try:
            ipaddr = DatagramTools.extract_ip(dg)
            
        except ValueError:
            #Bad IP in datagram
            return False
            
        if ipaddr.is_loopback: 
            return True
        
        # Consider Docker host as the local machine as well
        return any(ipaddr in network for network in self.docker_bridge_ranges)
        
        return False