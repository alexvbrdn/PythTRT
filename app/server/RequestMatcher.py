import re
from enum import Enum
from typing import List

from app.server.Request import Request


class Policy(str, Enum):
    FORBID = "forbid"
    ALLOW = "allow"
    DEPRIORITIZE = "deprioritize"
    PRIORITIZE = "prioritize"


class RequestMatcher:
    OBJECT_SERIALIZATION_DATA = [
        ("policy", "policy", Policy, True),
        ("domains_re", "domains_re_str", str, False),
        ("ports", "ports", int, False)
    ]

    def __init__(self, policy=Policy.FORBID):
        self.policy = policy
        self._domains_re = []
        self.domains_re_str = []
        self.ports = []

    def add_port(self, port: int):
        self.ports.append(port)
        return self

    def add_ports(self, ports: list):
        for port in ports:
            self.add_port(port)
        return self

    def add_domain_re(self, domain_re_str: str):
        self.domains_re_str.append(domain_re_str)
        self._domains_re.append(re.compile(domain_re_str))
        return self

    def add_domains_re(self, domains_re_str: List[str]):
        for domain_re_str in domains_re_str:
            self.add_domain_re(domain_re_str)
        return self

    def serializer_update_object(self):
        self._domains_re = []
        for domain_re_str in self.domains_re_str:
            self._domains_re.append(re.compile(domain_re_str))

    def request_match(self, request: Request) -> bool:
        if len(self.ports) != 0 and request.port not in self.ports:
            return False

        if len(self._domains_re) == 0:
            return True

        for domain_re in self._domains_re:
            if domain_re.match(request.domain):
                return True
        return False
