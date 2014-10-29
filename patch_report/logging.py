import sys


_VERBOSE = False


def set_verbose(verbose):
    global _VERBOSE
    _VERBOSE = verbose


def is_verbose():
    return _VERBOSE


def log(msg):
    if _VERBOSE:
        print >> sys.stderr, msg
