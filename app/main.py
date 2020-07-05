import optparse
import signal

from app.server.Logger import logger
from app.configuration import load_server


def signal_handler(sig, frame):
    server.stop()


signal.signal(signal.SIGINT, signal_handler)

parser = optparse.OptionParser()
parser.add_option('-i', '--input', action="store", dest="input", default="basic.json")
parser.add_option('-l', '--log', action="store", dest="log", default=None)

if __name__ == '__main__':
    options, args = parser.parse_args()
    if options.input is None:
        raise Exception("")

    if options.log is not None:
        logger.set_output(options.log)

    server = load_server(options.input)

    server.start()
