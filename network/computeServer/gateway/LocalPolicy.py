import ipaddress

from . import FilterPolicy

class LocalPolicy(FilterPolicy.FilterPolicy):
    # Override parent hook
    def _policy_hook(self, dg):
        return self._source_is_local_machine(dg)
        
    def _source_is_local_machine(self, dg):
        ipaddr = None
        try:
            ipaddr = self._extract_ip(dg)
            
        except ValueError:
            #Bad IP in datagram
            return False
            
        if ipaddr.is_loopback: return True
        
        return False