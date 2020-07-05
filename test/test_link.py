from unittest import TestCase

import socks

from app.server.Link import Link, PriorityLevel
from app.server.Logger import Logger
from app.server.Request import Request
from app.server.RequestMatcher import RequestMatcher, Policy


class TestLink(TestCase):
    def setUp(self) -> None:
        self.logger = Logger()

    def test_should_forbid_request_if_domain_is_in_blacklist(self):
        link = Link()
        matcher = RequestMatcher(Policy.FORBID)
        matcher.add_domain_re(r'^.+\.com$')
        link.add_request_matcher(matcher)

        actual = link.get_request_priority_level(Request("google.com", 80))
        self.assertEqual(actual, PriorityLevel.FORBID)

    def test_should_forbid_request_if_domain_is_not_in_whitelist(self):
        link = Link()
        matcher = RequestMatcher(Policy.ALLOW)
        matcher.add_domain_re(r'^.+\.com$')
        link.add_request_matcher(matcher)

        actual = link.get_request_priority_level(Request("google.fr", 80))
        self.assertEqual(actual, PriorityLevel.FORBID)

    def test_should_forbid_request_if_domain_in_whitelist_and_in_blacklist(self):
        link = Link()
        matcher = RequestMatcher(Policy.ALLOW)
        matcher.add_domain_re(r'^.+\.com$')
        link.add_request_matcher(matcher)

        matcher = RequestMatcher(Policy.FORBID)
        matcher.add_domain_re(r'^.+\.com$')
        link.add_request_matcher(matcher)

        actual = link.get_request_priority_level(Request("google.com", 80))
        self.assertEqual(actual, PriorityLevel.FORBID)

    def test_should_give_normal_priority_if_no_matcher_is_given(self):
        link = Link()

        actual = link.get_request_priority_level(Request("google.com", 80))
        self.assertEqual(actual, PriorityLevel.NORMAL)

    def test_should_give_normal_priority_if_prioritized_and_deprioritized_at_the_same_time(self):
        link = Link()
        matcher = RequestMatcher(Policy.ALLOW)
        matcher.add_domain_re(r'^.+\.com$')
        link.add_request_matcher(matcher)

        matcher = RequestMatcher(Policy.FORBID)
        matcher.add_domain_re(r'^.+\.com$')
        link.add_request_matcher(matcher)

        actual = link.get_request_priority_level(Request("google.com", 80))
        self.assertEqual(actual, PriorityLevel.FORBID)

    def test_should_give_low_priority_if_matcher_says_so(self):
        link = Link()
        matcher = RequestMatcher(Policy.DEPRIORITIZE)
        matcher.add_domain_re(r'^.+\.com$')
        link.add_request_matcher(matcher)

        actual = link.get_request_priority_level(Request("google.com", 80))
        self.assertEqual(actual, PriorityLevel.LOW)

    def test_should_give_high_priority_if_matcher_says_so(self):
        link = Link()
        matcher = RequestMatcher(Policy.PRIORITIZE)
        matcher.add_domain_re(r'^.+\.com$')
        link.add_request_matcher(matcher)

        actual = link.get_request_priority_level(Request("google.com", 80))
        self.assertEqual(actual, PriorityLevel.HIGH)

    def test_open_and_close_connection_link(self):
        link = Link()

        self.assertEqual(len(link.connections), 0)

        socket_connection = link.open_connection("1")
        self.assertEqual(len(link.connections), 1)
        self.assertFalse(socket_connection._closed)
        self.assertIsInstance(socket_connection, socks.socksocket)

        link.close_connection("1")
        self.assertEqual(len(link.connections), 0)
        self.assertTrue(socket_connection._closed)
