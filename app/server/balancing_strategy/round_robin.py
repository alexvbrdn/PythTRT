from typing import List

from app.server.Link import Link


def get_next_link(links: List[Link], **kwargs) -> Link:
    last_link = kwargs.get('last_link', None)
    if last_link is None:
        return links[0]
    next_link_idx = (links.index(last_link) + 1) % len(links)
    return links[next_link_idx]