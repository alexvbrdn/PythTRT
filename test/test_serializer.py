from unittest import TestCase

from app.configuration import save_server
from app.configuration.serializer import serialize, deserialize
from app.server import Server
from app.server.Balancer import Balancer, Strategy
from app.server.Link import Link
from app.server.RequestMatcher import RequestMatcher, Policy


class TestSerialize(TestCase):
    def test_serialize(self):
        req_matcher10 = RequestMatcher(policy=Policy.PRIORITIZE) \
            .add_domain_re(r'^intranet$') \
            .add_port(443)
        req_matcher11 = RequestMatcher(policy=Policy.PRIORITIZE) \
            .add_domain_re(r'^server-test$') \
            .add_port(8080)
        link1 = Link(interface="wlp5s0") \
            .add_request_matcher(req_matcher10) \
            .add_request_matcher(req_matcher11)
        req_matcher2 = RequestMatcher(policy=Policy.FORBID) \
            .add_domain_re(r'.com$')
        link2 = Link(interface="enp3s0", weight=2) \
            .add_request_matcher(req_matcher2)
        balancer_req_matcher = RequestMatcher(policy=Policy.ALLOW) \
            .add_port(443) \
            .add_port(80) \
            .add_port(8080)
        balancer = Balancer(strategy=Strategy.LEAST_CONNECTIONS) \
            .add_request_matcher(balancer_req_matcher) \
            .add_link(link1) \
            .add_link(link2)
        server = Server() \
            .set_balancer(balancer)

        serialized = serialize(server)
        deserialized = deserialize(serialized, Server)

        self.assertEqual(serialized, serialize(deserialized))

        save_server("test.json", server)
