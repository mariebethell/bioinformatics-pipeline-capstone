import ipaddress

from network.computeServer.gateway.DatagramTools import DatagramTools

class FilterPolicy:
    def __init__(self):
        self.docker_bridge_range = ipaddress.ip_network('172.17.0.0/16')
    
    def allow_inbound_datagram(self, dg):
        try:
            # Reject blatently incorrect datagrams
            if not self._screen_datagram_integrity(dg): return False
            
            # Call hook so child classes can inject behavior into this function
            if True in [self._policy_hook(dg), self.enforce_container_origin(dg)]:
                return True
            
            return False
            
        except Exception as e:
            #Default to reject
            print(f"WARNING: Rejecting packet due to unhandled exception: {e}")
            return False
        
    def enforce_container_origin(self, dg):
        try:
            ipaddr = DatagramTools.extract_ip(dg)
            return ipaddr in self.docker_bridge_range
            
        except ValueError:
            # Bad IP
            return False
        
    def _policy_hook(self, dg):
        # Abstract method. Child is expected to implement this.
        raise NotImplementedError()
        
    def _screen_datagram_integrity(self, dg):
        return True
        raise NotImplementedError()