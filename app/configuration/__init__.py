from typing import Optional

from app.configuration.serializer import deserialize, serialize
from app.server import Server


def load_server(path_to_file: str) -> Optional[Server]:
    try:
        with open(path_to_file, "r") as config:
            json = config.read()
            server = deserialize(json, Server)
    except Exception as err:
        raise Exception("Error while trying to load the configuration file '{}': '{}'.".format(path_to_file, err))

    return server


def save_server(path_to_file: str, server: Server):
    try:
        json = serialize(server)
        with open(path_to_file, "w") as config:
            config.write(json)
    except Exception as err:
        raise Exception("Error while trying to save the configuration file '{}': '{}'.".format(path_to_file, err))
