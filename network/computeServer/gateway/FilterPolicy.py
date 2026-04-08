import ipaddress

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
            ipaddr = self._extract_ip(dg)
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
        
    def _extract_ip(self, dg):
        ipaddr = None
        try:
            # Assume first IP in proxy record is the source IP
            source = dg.META['HTTP_X_FORWARDED_FOR'].split(',')[0] 
            ipaddr = ipaddress.ip_address(source)
            
        except (KeyError, ValueError):
            try:
                # No proxy, fallback to direct address
                source = dg.META['REMOTE_ADDR']
                ipaddr = ipaddress.ip_address(source)
                
            except (KeyError, ValueError):
                # No IP given or bad IP. Reject.
                raise ValueError("Invalid IP given")
                
        return ipaddr