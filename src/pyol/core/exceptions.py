"""PyOL Exceptinos"""


__all__ = ['PyOLException', 'PyOLError']


class PyOLException(Exception):
    """Base class for exceptions"""


class PyOLError(PyOLException):
    """Base class for errors."""
