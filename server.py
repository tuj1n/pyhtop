# -*- coding: utf-8 -*-
import socket
import select
from request import Request
from util import load_config, dir_exist, log_err

EOL = b'\r\n\r\n'

connections = {}
requests = {}
CONFIG = load_config('config.json')


def init():
    if not dir_exist(CONFIG['root']):
        log_err('config of root error')

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', CONFIG['listen']))
server_socket.listen(10000)
server_socket.setblocking(False)

ep = select.epoll()
ep.register(server_socket.fileno(), select.EPOLLIN | select.EPOLLET)

print 'server start at port %d' % CONFIG['listen']
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
                    from handle import handle_request
                    handle_request(requests[file_no])
                    ep.modify(file_no, select.EPOLLOUT | select.EPOLLOUT)
            elif event & select.EPOLLOUT:
                try:
                    while len(requests[file_no].response_message) > 0:
                        n = connections[file_no].send(requests[file_no].response_message)
                        requests[file_no].response_message = requests[file_no].response_message[n:]
                except socket.error:
                    pass
                if len(requests[file_no].response_message) == 0:
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

