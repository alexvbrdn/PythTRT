import socket
import time
from enum import Enum
from typing import Optional, List

import socks

from app.server.Logger import logger
from app.server.Request import Request
from app.server.RequestMatcher import Policy, RequestMatcher


class PriorityLevel(str, Enum):
    FORBID = "forbid"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class Protocol(str, Enum):
    DIRECT = "direct"
    SOCKS5 = "socks5"
    SOCKS4 = "socks4"
    HTTP = "http"


PROTOCOLS = {
    "direct": None,
    "socks5": socks.SOCKS5,
    "socks4": socks.SOCKS4,
    "http": socks.HTTP
}

TEST_ADDRESS = "example.org"
TEST_PORT = 80


class Link:
    OBJECT_SERIALIZATION_DATA = [
        ("timeout", "_timeout", int, False),
        ("weight", "weight", int, False),
        ("interface", "_interface", str, False),
        ("protocol", "_protocol", Protocol, False),
        ("domain", "_domain", str, False),
        ("port", "_port", int, False),
        ("matchers", "_request_matchers", RequestMatcher, False)
    ]

    def __init__(self, interface="", protocol=Protocol.DIRECT, domain="", port=0, timeout=10, weight=1):
        self._interface = interface
        self._protocol = protocol
        self._domain = domain
        self._port = port
        self._timeout = timeout
        self.weight = weight
        self._request_matchers = []
        self.connections = {}
        self.status = True
        self.latency = 0

    def __del__(self):
        connections = [key for key in self.connections.keys()]
        for connection_id in connections:
            self.close_connection(connection_id)

    def __str__(self):
        str_representation = "Link:"
        if self._interface:
            str_representation += "{},".format(self._interface)
        if self._protocol != Protocol.DIRECT:
            str_representation += "{},".format(self._protocol.value)
        if self._domain:
            str_representation += "{}:{},".format(self._domain, self._port)
        str_representation += str(self.weight)
        return str_representation

    def add_request_matcher(self, request_matcher: RequestMatcher):
        self._request_matchers.append(request_matcher)
        return self

    def add_request_matchers(self, request_matchers: List[RequestMatcher]):
        for request_matcher in request_matchers:
            self.add_request_matcher(request_matcher)
        return self

    def get_request_priority_level(self, request: Request) -> PriorityLevel:
        is_prioritized = False
        is_deprioritized = False
        for request_matcher in self._request_matchers:
            is_matching = request_matcher.request_match(request)

            if not self.status or (request_matcher.policy == Policy.ALLOW and not is_matching) or (
                    request_matcher.policy == Policy.FORBID and is_matching):
                return PriorityLevel.FORBID

            if is_matching and request_matcher.policy == Policy.PRIORITIZE:
                is_prioritized = True
            elif is_matching and request_matcher.policy == Policy.DEPRIORITIZE:
                is_deprioritized = True

        if is_prioritized == is_deprioritized:
            return PriorityLevel.NORMAL

        if is_prioritized:
            return PriorityLevel.HIGH

        if is_deprioritized:
            return PriorityLevel.LOW

    def open_connection(self, connection_id: str) -> Optional[socks.socksocket]:
        if connection_id in self.connections:
            logger.error(str(self), "Connection id '{}' already in use for this link.".format(connection_id))
            return None
        self.connections[connection_id] = self._build_socket()
        return self.connections[connection_id]

    def close_connection(self, connection_id: str):
        if connection_id in self.connections:
            self.connections[connection_id].close()
            del self.connections[connection_id]
        return self

    def _build_socket(self) -> socks.socksocket:
        sock = socks.socksocket()
        if self._protocol != Protocol.DIRECT:
            sock.setproxy(PROTOCOLS[self._protocol.value], self._domain, self._port)
        if self._interface:
            sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_BINDTODEVICE,
                self._interface.encode()
            )
        sock.settimeout(self._timeout)
        return sock

    def update_latency_and_status(self):
        sock = self.open_connection("TEST_LINK")
        try:
            s_time = time.time()
            sock.connect((TEST_ADDRESS, TEST_PORT))
            sock.sendall(str.encode("GET / HTTP/1.1\r\nHost: {}\r\n\r\n".format(TEST_ADDRESS)))
            sock.recv(1024)
            self.latency = round(time.time() - s_time, 3)
            self.status = True
        except Exception as e:
            self.latency = 0
            self.status = False
            logger.warning(str(self),
                           "Connection error with {}:{}, exception: \"{}\".".format(TEST_ADDRESS, TEST_PORT, e))
        finally:
            self.close_connection("TEST_LINK")
