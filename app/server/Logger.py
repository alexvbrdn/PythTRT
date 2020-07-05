from datetime import datetime

from termcolor import colored


class Logger:
    def __init__(self, output="", error=True, warning=True, info=True):
        self.log_error = error
        self.log_warning = warning
        self.log_info = info
        self.file = None

        if output != "":
            try:
                self.file = open(output, 'a')
            except IOError:
                raise Exception("Can not access to {}.".format(output))

    def __del__(self):
        if self.file is not None:
            self.file.close()

    def set_output(self,  output: str):
        if output != "":
            try:
                self.file = open(output, 'a')
            except IOError:
                raise Exception("Can not access to {}.".format(output))

    def _write_message(self, key: str, value: str, color="white"):
        message = "[{}]-[{}]: {}".format(str(datetime.now()), key, value)
        if self.file is not None:
            self.file.write(message + "\n")
        else:
            print(colored(message, color))

    def error(self, key: str, value: str):
        if self.log_error:
            self._write_message(key, value, "red")

    def warning(self, key: str, value: str):
        if self.log_warning:
            self._write_message(key, value, "yellow")

    def info(self, key: str, value: str):
        if self.log_info:
            self._write_message(key, value, "white")


logger = Logger()
