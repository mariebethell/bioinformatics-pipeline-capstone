import ipaddress

class DatagramTools:
    @staticmethod
    def extract_ip(datagram):
        ipaddr = None
        try:
            # Assume first IP in proxy record is the source IP
            source = datagram.META['HTTP_X_FORWARDED_FOR'].split(',')[0] 
            ipaddr = ipaddress.ip_address(source)
            
        except (KeyError, ValueError):
            try:
                # No proxy, fallback to direct address
                source = datagram.META['REMOTE_ADDR']
                ipaddr = ipaddress.ip_address(source)
                
            except (KeyError, ValueError):
                # No IP given or bad IP. Reject.
                raise ValueError("Invalid IP given")
                
        return ipaddr