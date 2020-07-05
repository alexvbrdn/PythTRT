from unittest import TestCase

from app.server.RequestMatcher import RequestMatcher, Policy
from app.server.Request import Request

class TestRequestMatcher(TestCase):
    def test_should_match_request_when_empty(self):
        matcher = RequestMatcher(Policy.ALLOW)

        actual = matcher.request_match(Request("google.com", 80))

        self.assertTrue(actual)

    def test_should_match_request_when_domain_is_okay(self):
        matcher = RequestMatcher(Policy.ALLOW)
        matcher.add_domain_re(r'^.+\.com$')
        actual = matcher.request_match(Request("google.com", 80))

        self.assertTrue(actual)

    def test_should_not_match_request_when_domain_is_okay_but_not_port(self):
        matcher = RequestMatcher(Policy.ALLOW)
        matcher.add_domain_re(r'^.+\.com$')
        matcher.add_port(8080)
        actual = matcher.request_match(Request("google.com", 80))

        self.assertFalse(actual)

    def test_should_not_match_request_when_domain_is_not_okay(self):
        matcher = RequestMatcher(Policy.ALLOW)
        matcher.add_domain_re(r'^.+\.fr$')
        actual = matcher.request_match(Request("google.com", 80))

        self.assertFalse(actual)
