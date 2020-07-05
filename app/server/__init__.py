import select
import socket
import threading
from enum import Enum
from struct import unpack
from time import sleep
from typing import Optional

import socks

from app.server.Balancer import Balancer
from app.server.Link import Link
from app.server.Logger import logger
from app.server.Request import Request


class SocksCommand(Enum):
    CONNECT = b'\x01'
    BIND = b'\x02'
    UDP_ASSOCIATE = b'\x03'


class SocksAddressType(Enum):
    IPV4 = b'\x01'
    DOMAINNAME = b'\x03'
    IPV6 = b'\x04'


class SocksMethod(Enum):
    NO_AUTH = b'\x00'
    GSAPI = b'\x01'
    USERNAME_PASSWORD = b'\x02'
    NO_ACCEPTABLE_METHODS = b'\xff'


class SocksReply(Enum):
    SUCCEEDED = b'\x00'
    SERVER_FAILURE = b'\x01'
    CONNECTION_NOT_ALOWED = b'\x02'
    NETWORK_UNREACHABLE = b'\x03'
    HOST_UNREACHABLE = b'\x04'
    CONNECTION_REFUSED = b'\x05'
    TTL_EXPIRED = b'\x06'
    COMMAND_NOT_SUPPORTED = b'\x07'
    ADDRESS_TYPE_NOT_SUPPORTED = b'\x08'


# https://tools.ietf.org/html/rfc1928
class Server:
    OBJECT_SERIALIZATION_DATA = [
        ("balancer", "balancer", Balancer, True),
        ("domain", "domain", str, False),
        ("port", "port", int, False),
        ("timeout", "timeout", int, False),
        ("max_threads", "max_threads", int, False),
    ]

    def __init__(self, domain="0.0.0.0", port=1080, timeout=5, max_threads=200):
        self.balancer = None
        self.domain = domain
        self.port = port
        self.timeout = timeout
        self.max_threads = max_threads
        self._server_thread = None
        self._balancer_thread = None
        self.STOP = False
        self._link_counter = 0

    def __str__(self):
        return "Server:{}:{}".format(self.domain, self.port)

    def __del__(self):
        self.stop()

    def set_balancer(self, balancer: Balancer):
        self.balancer = balancer
        return self

    def start(self) -> bool:
        self.STOP = False
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.settimeout(self.timeout)
        except socket.error as err:
            logger.error(str(self), "Failed to create the socket server, error: \"{}\".".format(err))
            return False

        try:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.domain, self.port))
            logger.info(str(self), 'Bind {}.'.format(str(self.port)))
        except socket.error as err:
            server_socket.close()
            logger.error(str(self), "Cannot bind {}:{}, error: \"{}\".".format(self.domain, self.port, err))
            return False

        try:
            server_socket.listen(10)
        except socket.error as err:
            server_socket.close()
            logger.error(str(self), "Listen failed, error: \"{}\".".format(err))
            return False

        self._server_thread = threading.Thread(target=self._accept_client_loop, args=(server_socket,))
        self._server_thread.start()

        self._balancer_thread = threading.Thread(target=self._balancer_loop)
        self._balancer_thread.start()

        return True

    def stop(self):
        self.STOP = True

    def _balancer_loop(self):
        while not self.STOP:
            self.balancer.update_links_status()
            sleep(10)

    def _socks_sub_negotiation_choose_method(self, socket_client: socket) -> SocksMethod:
        try:
            methods_packet = socket_client.recv(2048)
        except socket.error:
            logger.error(str(self), "Socket error while trying to communicate with client.")
            return SocksMethod.NO_ACCEPTABLE_METHODS

        ver = methods_packet[0]
        nmethods = methods_packet[1]
        methods = methods_packet[2:]

        if ver != 5:
            logger.error(str(self), "SOCKS version '{}' not supported.".format(ver))
            return SocksMethod.NO_ACCEPTABLE_METHODS

        if nmethods != len(methods):
            logger.error(str(self), "Malformed SOCKS packet received from client.")
            return SocksMethod.NO_ACCEPTABLE_METHODS

        if ord(SocksMethod.NO_AUTH.value) in methods:
            return SocksMethod.NO_AUTH

        return SocksMethod.NO_ACCEPTABLE_METHODS

    def _socks_sub_negotiation_send_chosen_method(self, socket_client: socket, method: SocksMethod) -> bool:
        chosen_method_packet = b'\x05' + method.value
        try:
            socket_client.sendall(chosen_method_packet)
        except socket.error as err:
            logger.error(str(self), "Socket error while trying to communicate with client: \"{}\".".format(err))
            return False
        return True

    def _socks_sub_negotiation(self, socket_client: socket) -> bool:
        method = self._socks_sub_negotiation_choose_method(socket_client)
        self._socks_sub_negotiation_send_chosen_method(socket_client, method)
        if method == SocksMethod.NO_ACCEPTABLE_METHODS:
            return False
        return True

    def _socks_request_get_dest(self, socket_client: socket) -> (Optional[str], Optional[int]):
        try:
            request_packet = socket_client.recv(2048)
        except socket.error:
            logger.error(str(self), "Socket error while trying to communicate with client.")
            self._socks_request_send_reply(socket_client, SocksReply.SERVER_FAILURE)
            raise Exception()

        ver = request_packet[0]
        cmd = request_packet[1]
        atyp = request_packet[3]

        if ver != 5:
            logger.error(str(self), "SOCKS version '{}' not supported.".format(ver))
            self._socks_request_send_reply(socket_client, SocksReply.CONNECTION_REFUSED)
            return None

        if cmd != ord(SocksCommand.CONNECT.value):
            logger.error(str(self), "SOCKS command '{}' not supported.".format(cmd))
            self._socks_request_send_reply(socket_client, SocksReply.COMMAND_NOT_SUPPORTED)
            return None

        if atyp == ord(SocksAddressType.IPV4.value):
            dst_addr = socket.inet_ntop(socket.AF_INET, request_packet[4:-2])
        elif atyp == ord(SocksAddressType.DOMAINNAME.value):
            dst_addr = request_packet[5:-2].decode()
        elif atyp == ord(SocksAddressType.IPV6.value):
            dst_addr = socket.inet_ntop(socket.AF_INET6, request_packet[4:-2])
        else:
            logger.error(str(self), "SOCKS address type '{}' not supported.".format(atyp))
            self._socks_request_send_reply(socket_client, SocksReply.ADDRESS_TYPE_NOT_SUPPORTED)
            return None

        dst_port = unpack('>H', request_packet[-2:])[0]

        return dst_addr, dst_port

    def _socks_request_send_reply(self, socket_client: socket, reply: SocksReply) -> bool:
        reply_packet = b'\x05' + reply.value + b'\x00' + SocksAddressType.IPV4.value + \
                       b'\x00' + b'\x00' + b'\x00' + b'\x00' + \
                       b'\x00' + b'\x00'
        try:
            socket_client.sendall(reply_packet)
        except socket.error as err:
            logger.error(str(self), "Socket error while trying to communicate with client: \"{}\".".format(err))
            return False
        return True

    def _socks_request(self, socket_client: socket) -> (Optional[Link], Optional[int], Optional[socks.socksocket]):
        (domain, port) = self._socks_request_get_dest(socket_client)
        request = Request(domain, port)
        link = self.balancer.get_next_link(request)
        if link is None:
            logger.error(str(self), "No Link available to handle the request.")
            return None
        connection_id = self.generate_connection_id()
        socket_link = link.open_connection(connection_id)
        if socket_link is None:
            link.close_connection(connection_id)
            return None
        try:
            socket_link.connect((domain, port))
        except socket.error as err:
            logger.error(str(self),
                         "Socket error while trying to connect to {}:{}: \"{}\".".format(domain, port, err))
            link.close_connection(connection_id)
            self._socks_request_send_reply(socket_client, SocksReply.NETWORK_UNREACHABLE)
            return None

        if not self._socks_request_send_reply(socket_client, SocksReply.SUCCEEDED):
            link.close_connection(connection_id)
            return None

        return link, connection_id, socket_link

    def generate_connection_id(self) -> str:
        connection_id = str(self._link_counter)
        self._link_counter += 1
        return connection_id

    def _accept_client_loop(self, server_socket: socket):
        logger.info(str(self), "Ready to receive requests.")
        while not self.STOP:
            if threading.active_count() > self.max_threads:
                sleep(5)  # It means that the thread will take 5 seconds maximum to return
                continue

            try:
                client_socket, _ = server_socket.accept()
                client_socket.setblocking(True)
            except socket.timeout:
                continue
            except socket.error:
                continue
            except TypeError as err:
                logger.error(str(self), "Error: \"{}\".".format(err))
                return
            exchange_thread = threading.Thread(target=self.handle_request, args=(client_socket,))
            exchange_thread.start()
        server_socket.close()
        logger.info(str(self), "Stopping server.")

    def handle_request(self, socket_client: socket):
        if not self._socks_sub_negotiation(socket_client):
            return
        request = self._socks_request(socket_client)
        if request is None:
            return
        link, connection_id, socket_link = request
        self._exchange_with_client(socket_client, socket_link)
        socket_client.close()
        link.close_connection(connection_id)
        return

    def _exchange_with_client(self, socket_client: socket, socket_link: socks.socksocket):
        while not self.STOP:
            try:
                reader, _, _ = select.select([socket_client, socket_link], [], [], socket_link.gettimeout())
            except select.error as err:
                logger.error(str(self), "Select failed: \"{}\".".format(err))
                return
            if not reader:
                return
            try:
                for sock in reader:
                    data = sock.recv(2048)
                    if not data:
                        return
                    if sock is socket_link:
                        socket_client.send(data)
                    else:
                        socket_link.send(data)
            except socket.error as err:
                logger.error(str(self),
                             "Socket error while trying to communicate with client: \"{}\".".format(err))
                return
