from unittest import TestCase

from RequestMatcher import RequestMatcher, Policy
from app.server.Balancer import Balancer, Strategy
from app.server.Link import Link
from app.server.Request import Request


class TestBalancer(TestCase):
    def test_should_return_next_link_in_round_robin(self):
        expected_first_link = Link(domain="Link1", port=1080)
        expected_second_link = Link(domain="Link2", port=1081)
        expected_third_link = Link(domain="Link3", port=1082)

        balancer = Balancer() \
            .set_strategy(Strategy.ROUND_ROBIN) \
            .add_link(expected_first_link) \
            .add_link(expected_second_link) \
            .add_link(expected_third_link)

        actual_first_link = balancer.get_next_link(Request('test', 80))
        self.assertEqual(actual_first_link, expected_first_link)

        actual_second_link = balancer.get_next_link(Request('test', 80))
        self.assertEqual(actual_second_link, expected_second_link)

        actual_third_link = balancer.get_next_link(Request('test', 80))
        self.assertEqual(actual_third_link, expected_third_link)

        actual_first_link = balancer.get_next_link(Request('test', 80))
        self.assertEqual(expected_first_link, actual_first_link)

    def test_should_block_request(self):
        expected_link = Link(domain="Link1", port=1080)

        matcher = RequestMatcher(policy=Policy.FORBID)\
            .add_port(80)

        balancer = Balancer() \
            .set_strategy(Strategy.ROUND_ROBIN) \
            .add_link(expected_link)\
            .add_request_matcher(matcher)

        should_be_none = balancer.get_next_link(Request('test', 80))
        self.assertIsNone(should_be_none)

    def test_should_allow_request(self):
        expected_link = Link(domain="Link1", port=1080)

        matcher = RequestMatcher(policy=Policy.ALLOW)\
            .add_port(80)

        balancer = Balancer() \
            .set_strategy(Strategy.ROUND_ROBIN) \
            .add_link(expected_link)\
            .add_request_matcher(matcher)

        should_be_link = balancer.get_next_link(Request('test', 80))
        self.assertEqual(expected_link, should_be_link)
