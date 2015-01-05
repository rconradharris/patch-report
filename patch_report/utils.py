import contextlib
import datetime
import errno
import os
import shutil


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


class PIDFileExists(Exception):
    pass


@contextlib.contextmanager
def pidfile_guard(filename):
    if os.path.exists(filename):
        raise PIDFileExists(filename)

    with open(filename, 'w') as f:
        f.write(str(os.getpid()))

    try:
        yield
    finally:
        os.unlink(filename)
