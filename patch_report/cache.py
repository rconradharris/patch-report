import os
import pickle
import tempfile

from patch_report import config
from patch_report import utils


class CacheFileNotFound(Exception):
    pass


def _make_filename(name):
    cachedir = config.get('patch_report', 'cache_directory')
    return os.path.join(cachedir, '%s.pickle' % name)


def read_file(name):
    filename = _make_filename(name)

    if not os.path.exists(filename):
        raise CacheFileNotFound(filename)

    with open(filename) as f:
        return pickle.load(f)


def write_file(name, data):
    filename = _make_filename(name)
    tmpfile = tempfile.NamedTemporaryFile(delete=False)
    try:
        with tmpfile:
            pickle.dump(data, tmpfile)
    except:
        os.unlink(tmpfile.name)
    else:
        os.rename(tmpfile.name, filename)


def get_last_updated_at(name):
    filename = _make_filename(name)
    return utils.get_file_modified_time(filename)
