# coding=utf-8
import logging


class Message(object):
    def __init__(self, fmt, args):
        self.fmt = fmt
        self.args = args

    def __str__(self):
        return self.fmt.format(*self.args)


class StyleAdapter(logging.LoggerAdapter):
    """Allows to use braced placeholders in logging statements. The format magic happens in Message.

    Usage:
    Wrap the handler returned by logging.getLogger(__name__) with the
    StyleAdapter. Do this in every submodule if necessary.

        log = StyleAdapter(logging.getLogger(__name__))

    See https://docs.python.org/3/howto/logging-cookbook.html#use-of-alternative-formatting-styles
    """

    def __init__(self, logger, extra=None):
        super(StyleAdapter, self).__init__(logger, extra or {})

    def log(self, level, msg, *args, **kwargs):
        if self.isEnabledFor(level):
            msg, kwargs = self.process(msg, kwargs)
            self.logger._log(level, Message(msg, args), (), **kwargs)
