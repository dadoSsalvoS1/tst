import socket

def get_local_ip():
    """
    Detects the local IP address of the machine by creating a dummy socket connection.
    This works even without internet access as long as there is a network interface.
    """
    try:
        # Create a dummy socket to connect to an external IP (Google DNS)
        # This forces the OS to choose the correct outbound interface.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # We don't actually need to connect to 8.8.8.8, just attempt routing
            s.connect(('8.8.8.8', 1))
            local_ip = s.getsockname()[0]
        except Exception:
            local_ip = '127.0.0.1'
        finally:
            s.close()
        return local_ip
    except Exception:
        return '127.0.0.1'
