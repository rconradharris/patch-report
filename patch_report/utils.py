import contextlib
import datetime
import errno
import os
import shutil
import sys

from patch_report.simplelog import log


def makedirs_ignore_exists(*args, **kwargs):
    try:
        os.makedirs(*args, **kwargs)
    except os.error as e:
        if e.errno != errno.EEXIST:
            raise


def rmtree_ignore_exists(path, *args, **kwargs):
    if os.path.exists(path):
        shutil.rmtree(path)


@contextlib.contextmanager
def temp_chdir(dirname):
    orig_path = os.getcwd()
    os.chdir(dirname)
    try:
        yield
    finally:
        os.chdir(orig_path)


def get_file_modified_time(path):
    if not os.path.exists(path):
        return None

    epoch_secs = os.path.getmtime(path)
    return datetime.datetime.utcfromtimestamp(epoch_secs)


def pidfile_guard(filename):
    if os.path.exists(filename):
        log("pidfile '%s' exists, exiting..." % filename)
        sys.exit(0)


@contextlib.contextmanager
def pidfile_context(filename):
    with open(filename, 'w') as f:
        f.write(str(os.getpid()))

    try:
        yield
    finally:
        os.unlink(filename)
