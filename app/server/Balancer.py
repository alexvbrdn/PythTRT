from typing import Optional, List

from app.server.Link import Link, PriorityLevel
from app.server.Logger import logger
from app.server.Request import Request
from app.server.RequestMatcher import RequestMatcher, Policy
from app.server.balancing_strategy import Strategy, get_next_link


class Balancer:
    OBJECT_SERIALIZATION_DATA = [
        ("strategy", "strategy", Strategy, False),
        ("links", "links", Link, True),
        ("matchers", "_request_matchers", RequestMatcher, False)
    ]

    def __init__(self, strategy=Strategy.ROUND_ROBIN):
        self.strategy = strategy
        self.links = []
        self._request_matchers = []
        self._last_link = None

    def __str__(self):
        return "Balancer:{},{}".format(self.strategy, self.links.__len__())

    def add_link(self, link: Link):
        self.links.append(link)
        return self

    def add_links(self, links: list):
        for link in links:
            self.add_link(link)
        return self

    def set_strategy(self, strategy: Strategy):
        self.strategy = strategy
        return self

    def add_request_matcher(self, request_matcher: RequestMatcher):
        self._request_matchers.append(request_matcher)
        return self

    def add_request_matchers(self, request_matchers: List[RequestMatcher]):
        for request_matcher in request_matchers:
            self.add_request_matcher(request_matcher)
        return self

    def get_link_ids_for_request(self, request: Request) -> (list, list, list):
        high_priority = []
        normal_priority = []
        low_priority = []
        for link_id, link in enumerate(self.links):
            priority_level = link.get_request_priority_level(request)
            if priority_level == PriorityLevel.HIGH:
                high_priority.append(link_id)
            elif priority_level == PriorityLevel.NORMAL:
                normal_priority.append(link_id)
            elif priority_level == PriorityLevel.LOW:
                low_priority.append(link_id)

        return high_priority, normal_priority, low_priority

    def get_next_link(self, request: Request) -> Optional[Link]:
        if not self.should_accept_request(request):
            logger.error(str(self), "Request {} rejected.".format(request))
            return None

        high_priority, normal_priority, low_priority = self.get_link_ids_for_request(request)

        if len(high_priority) != 0:
            links_id = high_priority
        elif len(normal_priority) != 0:
            links_id = normal_priority
        elif len(low_priority) != 0:
            links_id = low_priority
        else:
            logger.error(str(self), "No link available to take this request ({}).".format(request))
            return None

        links = [self.links[link_id] for link_id in links_id]

        self._last_link = get_next_link(links, self._last_link, self.strategy)

        return self._last_link

    def update_links_status(self):
        for link in self.links:  # TODO: Parallelize iterations
            link.update_latency_and_status()

    def should_accept_request(self, request: Request) -> bool:
        for request_matcher in self._request_matchers:
            is_matching = request_matcher.request_match(request)

            if (request_matcher.policy == Policy.ALLOW and not is_matching) or (
                    request_matcher.policy == Policy.FORBID and is_matching):
                return False
        return True
