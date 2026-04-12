import ipaddress

from rest_framework.request import Request

class DatagramTools:
    """
    Tools used by FilterPolicies to perform repetitive tasks

    """

    @staticmethod
    def extract_ip(datagram: Request) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
        """
        Extracts and parses the source IP from a request
            - Uses source data from NIC or reverse proxy, not whatever the sender put in there

        Args:
            datagram (rest_framework.request) to pull IP from

        Returns:
            The extracted ipaddress object, which could be IPv4Address or IPv6Address

        Raises:
            ValueError if IP in request is invalid

        """

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