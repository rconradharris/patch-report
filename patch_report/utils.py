import contextlib
import datetime
import os


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
