# -*- coding: utf-8 -*-
from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO
from util import CLRF, STATUS_MESSAGE, SERVER_STR
from response import err_page
from header_handler import *
import time

header_handler = {
    'host': host_handler,
    'connection': connection_handler,
    'user_agent': user_agent_handler,
    'if-modified_since': if_modified_since_handler
}


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = StringIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message


def handle_request(request):
    result = RequestHandler(request.get_message())

    request.path = result.path
    request.method = result.command
    request.version = result.request_version

    for key in result.headers.keys():
        request.headers[key] = result.headers[key]

    for key in request.headers.keys():
        print 'key:%s value:%s' % (key, request.headers[key])

    # only support GET now.
    if not valid_method(request.method) or request.method != 'GET':
        request.response_message = build_err_response(request, 405)


def handle_response(request):
    if request.response_done:
        pass


def valid_method(method):
    methods = ('GET', 'POST', 'PUT', 'CONNECT', 'HEAD', 'OPTIONS', 'TRACE', 'DELETE')
    if method in methods:
        return True
    return False


def build_err_response(request, status):
    # HTTP/1.1 404 Not Found\r\n
    response_line = '%s %s%s' % (request.version, STATUS_MESSAGE[status], CLRF)

    headers = ''
    headers += 'Date: %s%s' % (time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.localtime()), CLRF)
    headers += 'Server: %s%s' % (SERVER_STR, CLRF)
    headers += 'Content-Type: text/html%s' % CLRF
    content = err_page(status)
    headers += 'Content-Length: %d%s%s' % (len(content), CLRF, CLRF)

    response = response_line + headers + content
    # response build done
    request.response_done = True
    return response


def handle_uri(request):
    print request.path


def header_handler(request, header):
    pass
