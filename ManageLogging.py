import GlobalVariables
import logging
from logging.handlers import TimedRotatingFileHandler

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

# The background is set with 40 plus the number of the color, and the foreground with 30

# These are the sequences need to get colored output
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"


def formatter_message(message, use_color=True):
    if use_color:
        message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
    else:
        message = message.replace("$RESET", "").replace("$BOLD", "")
    return message


COLORS = {
    'WARNING': YELLOW,
    'INFO': MAGENTA,
    'DEBUG': BLUE,
    'CRITICAL': CYAN,
    'ERROR': RED
}


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)


# Custom logger class with multiple destinations
class ColoredLogger(logging.Logger):
    FORMAT_LOG = "%(asctime)s [%(levelname)-8s]  %(message)s (%(filename)s:%(lineno)d)"
    COLOR_LOG_FORMAT = formatter_message(FORMAT_LOG, True)
    FORMAT_CONSOLE = "%(message)s"
    COLOR_CONSOLE_FORMAT = formatter_message(FORMAT_CONSOLE, True)

    def __init__(self, name):
        logging.Logger.__init__(self, name, logging.DEBUG)

        color_log_formatter = ColoredFormatter(self.COLOR_LOG_FORMAT)
        color_console_formatter = ColoredFormatter(self.COLOR_CONSOLE_FORMAT)

        console = logging.StreamHandler()
        console.setFormatter(color_console_formatter)
        console.setLevel(logging.INFO)

        # Add the log message handler to the logger
        log = logging.handlers.RotatingFileHandler(GlobalVariables.path_to_save_log)
        log.setFormatter(color_log_formatter)
        log.setLevel(logging.DEBUG)

        self.addHandler(console)
        self.addHandler(log)
        return