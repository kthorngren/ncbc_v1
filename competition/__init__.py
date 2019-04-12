

# create logger
import logging
import os


def get_logger(name, level=''):
    #print(name)

    if level:
        LEVEL = validate_level(level)
    else:
        LEVEL = logging.ERROR

    logger = logging.getLogger(name)

    logger.setLevel(LEVEL)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(LEVEL)

    # create formatter
    formatter = logging.Formatter('%(asctime)s.%(msecs)03d: %(levelname)s: %(module)s.%(funcName)s(): %(message)s', datefmt='%m-%d-%Y %H:%M:%S')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    # end create logger

    logging.captureWarnings(True)  # eliminate the insecure warnings on the console
    return logger

def validate_level(level):

    levels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']

    if isinstance(level, str) and level.upper() in levels:
        return level.upper()
    return 'ERROR'


def set_log_level(logger, level):

    level = validate_level(level)

    logger.setLevel(level)
    logger.handlers[0].setLevel(level)

    return logger
