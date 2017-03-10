# -*- coding: utf-8 -*-
import socket
import select
from handle import handle_request
from request import Request

EOL = b'\r\n\r\n'
response = b'HTTP/1.0 200 OK\r\nDate: Mon, 1 Jan 1996 01:01:01 GMT\r\n'
response += b'Content-Type: text/plain\r\nContent-Length: 13\r\n\r\n'
response += b'Hello, world!'

connections = {}
requests = {}
responses = {}

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 8080))
server_socket.listen(10000)
server_socket.setblocking(False)

ep = select.epoll()
ep.register(server_socket.fileno(), select.EPOLLIN | select.EPOLLET)

try:
    while True:
        events = ep.poll(1)  # timeout = 1s
        for file_no, event in events:
            # new connection
            if file_no == server_socket.fileno():
                try:
                    while True:
                        connection, address = server_socket.accept()
                        connection.setblocking(False)
                        ep.register(connection.fileno(), select.EPOLLIN | select.EPOLLET)
                        connections[connection.fileno()] = connection
                        request = Request(connection.fileno())
                        requests[connection.fileno()] = request
                        responses[connection.fileno()] = response
                except socket.error:    # EAGAIN
                    pass
            elif event & select.EPOLLIN:
                try:
                    while True:
                        requests[file_no].append_message(connections[file_no].recv(1024))
                except socket.error:
                    pass
                # receive done
                if EOL in requests[file_no].get_message():
                    # parser request
                    handle_request(requests[file_no])
                    ep.modify(file_no, select.EPOLLOUT | select.EPOLLOUT)
            elif event & select.EPOLLOUT:
                try:
                    while len(responses[file_no]) > 0:
                        byteswritten = connections[file_no].send(responses[file_no])
                        responses[file_no] = responses[file_no][byteswritten:]
                except socket.error:
                    pass
                if len(responses[file_no]) == 0:
                    ep.modify(file_no, select.EPOLLET)
                    connections[file_no].close()
                    del connections[file_no]
            elif event & select.EPOLLHUP:
                ep.unregister(file_no)
                connections[file_no].close()
                del connections[file_no]
finally:
    ep.unregister(server_socket.fileno())
    ep.close()
    server_socket.close()

