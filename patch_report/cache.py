import os
import pickle
import tempfile

from patch_report import config
from patch_report import utils


class CacheFileNotFound(Exception):
    pass


def _make_cache_directory():
    cachedir = config.get('patch_report', 'cache_directory')
    return os.path.join(cachedir, 'patch_report')


def _make_filename(name):
    cachedir = _make_cache_directory()
    return os.path.join(cachedir, '%s.pickle' % name)


def read_file(name):
    filename = _make_filename(name)

    if not os.path.exists(filename):
        raise CacheFileNotFound(filename)

    with open(filename) as f:
        return pickle.load(f)


def write_file(name, data):
    cachedir = _make_cache_directory()
    utils.makedirs_ignore_exists(cachedir)

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


def clear():
    cachedir = _make_cache_directory()
    utils.rmtree_ignore_exists(cachedir)


class DictCache(object):
    def __init__(self, filename):
        self.filename = filename
        self.data = None

    def _load(self):
        try:
            self.data = read_file(self.filename)
        except CacheFileNotFound:
            self.data = {}

    def __getitem__(self, key):
        if self.data is None:
            self._load()

        return self.data[key]

    def __setitem__(self, key, value):
        if self.data is None:
            self._load()

        self.data[key] = value
        write_file(self.filename, self.data)