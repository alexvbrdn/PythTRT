from random import choice
from typing import List

from app.server.Link import Link


def get_next_link(links: List[Link]) -> Link:
    weighted_links_idx = []
    for idx, element in enumerate(links):
        for _ in range(0, element.weight):
            weighted_links_idx.append(idx)
    return links[choice(weighted_links_idx)]