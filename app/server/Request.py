from enum import Enum


class DomainType(str, Enum):
    DOMAIN = "domain"
    IPV4 = "ipv4"
    IPV6 = "ipv6"


class Request:
    def __init__(self, domain: str, port: int):
        self.domain = domain
        self.port = port

    def __str__(self):
        return "{}:{}".format(self.domain, self.port)
