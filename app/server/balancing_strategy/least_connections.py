from typing import List

from app.server.Link import Link


def get_next_link(links: List[Link]) -> Link:
    links_count = [len(link.connections) / link.weight for link in links]
    return links[links_count.index(min(links_count))]
