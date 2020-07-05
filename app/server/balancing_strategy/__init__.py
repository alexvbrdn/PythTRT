from enum import Enum
from importlib import import_module
from typing import List, Optional

from app.server.Link import Link


class Strategy(str, Enum):
    ROUND_ROBIN = "round_robin"
    RANDOM_LINK = "random_link"
    LEAST_CONNECTIONS = "least_connections"


def get_next_link(links: List[Link], last_link: Optional[Link], strategy: Strategy):
    module = import_module(strategy)
    return module.get_next_link(links, last_link=last_link)
