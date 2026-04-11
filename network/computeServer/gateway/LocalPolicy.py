import ipaddress

from network.computeServer.gateway import FilterPolicy
from network.computeServer.gateway.DatagramTools import DatagramTools

class LocalPolicy(FilterPolicy.FilterPolicy):
    # Override parent hook
    def _policy_hook(self, dg):
        return self._source_is_local_machine(dg)
        
    def _source_is_local_machine(self, dg):
        ipaddr = None
        try:
            ipaddr = DatagramTools.extract_ip(dg)
            
        except ValueError:
            #Bad IP in datagram
            return False
            
        if ipaddr.is_loopback: 
            return True
        
        return False