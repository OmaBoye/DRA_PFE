# test_tls.py
import socket
import ssl

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE  # For testing only (disable in production)

with socket.create_connection(('localhost', 2575)) as sock:
    with context.wrap_socket(sock, server_hostname='localhost') as ssock:
        ssock.sendall(b"Test message")
        print(ssock.recv(4096))