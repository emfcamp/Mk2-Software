import logging
import datetime
import sys
from structlog.processors import JSONRenderer
from structlog import wrap_logger
from structlog.stdlib import filter_by_level


def add_timestamp(_, __, event_dict):
    event_dict['time'] = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    return event_dict


def get_wrapped_logger():
    return wrap_logger(
        logging.getLogger(__name__),
        processors=[
            filter_by_level,
            add_timestamp,
            JSONRenderer(separators=(', ', ':'), sort_keys=True)
        ]
    )


def get_get_logger():
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format='%(message)s'
    )
    return get_wrapped_logger
