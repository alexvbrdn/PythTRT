from unittest import TestCase

from app.server.Link import Link
from app.server.balancing_strategy import least_connections, round_robin, random_link


class TestStrategy(TestCase):
    def test_round_robin_should_return_next_one(self):
        link_1 = Link()
        link_2 = Link()
        link_3 = Link()

        links = [link_1, link_2, link_3]

        actual = round_robin.get_next_link(links, last_link=link_1)

        self.assertEqual(actual, link_2)

    def test_round_robin_should_return_the_first_after_the_last_one(self):
        link_1 = Link()
        link_2 = Link()
        link_3 = Link()

        links = [link_1, link_2, link_3]

        actual = round_robin.get_next_link(links, last_link=link_3)

        self.assertEqual(actual, link_1)

    def test_round_robin_should_return_the_first_one_when_no_last_link(self):
        link_1 = Link()
        link_2 = Link()
        link_3 = Link()

        links = [link_1, link_2, link_3]

        actual = round_robin.get_next_link(links)

        self.assertEqual(actual, link_1)

    def test_should_return_random_idx(self):
        link_1 = Link()
        link_2 = Link()
        link_3 = Link()

        links = [link_1, link_2, link_3]

        next_linkA = random_link.get_next_link(links)
        next_linkB = random_link.get_next_link(links)
        next_linkC = random_link.get_next_link(links)
        next_linkD = random_link.get_next_link(links)
        next_linkE = random_link.get_next_link(links)

        self.assertFalse(next_linkA == next_linkB == next_linkC == next_linkD == next_linkE)

    def test_should_almost_always_return_element(self):
        link_1 = Link(weight=1)
        link_2 = Link(weight=100000)
        link_3 = Link(weight=1)

        links = [link_1, link_2, link_3]

        next_link = random_link.get_next_link(links)

        self.assertEqual(next_link, link_2)

    def test_least_connections_should_return_the_link_with_least_connections(self):
        link_1 = Link()
        link_2 = Link()
        link_3 = Link()

        link_1.open_connection("1")
        link_3.open_connection("1")

        links = [link_1, link_2, link_3]

        actual = least_connections.get_next_link(links)
        self.assertEqual(actual, link_2)

    def test_least_connections_should_return_the_link_with_least_connections_by_using_weight(self):
        link_1 = Link()
        link_2 = Link(weight=2)
        link_3 = Link()

        link_1.open_connection("1")
        link_2.open_connection("1")
        link_3.open_connection("1")

        links = [link_1, link_2, link_3]

        actual = least_connections.get_next_link(links)
        self.assertEqual(actual, link_2)
