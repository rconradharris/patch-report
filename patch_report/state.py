import os
try:
    import cPickle as pickle
except ImportError:
    import pickle
import tempfile

from patch_report import config
from patch_report.simplelog import log
from patch_report import utils


class FileNotFound(Exception):
    pass


class StateDirectory(object):
    def __init__(self, subdirectory=None):
        statedir = config.get('patch_report', 'state_directory')
        self.directory = os.path.join(statedir, 'patch_report')

        if subdirectory:
            self.directory = os.path.join(self.directory, subdirectory)

    def _make_filename(self, name):
        return os.path.join(self.directory, '%s.pickle' % name)

    def read_file(self, name):
        filename = self._make_filename(name)

        if not os.path.exists(filename):
            raise FileNotFound(filename)

        with open(filename) as f:
            return pickle.load(f)

    def write_file(self, name, data):
        utils.makedirs_ignore_exists(self.directory)

        filename = self._make_filename(name)

        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        try:
            with tmpfile:
                pickle.dump(data, tmpfile)
        except:
            os.unlink(tmpfile.name)
            raise
        else:
            os.rename(tmpfile.name, filename)

    def get_last_updated_at(self, name):
        filename = self._make_filename(name)
        return utils.get_file_modified_time(filename)

    def clear(self):
        log('Clearing the cache...')
        utils.rmtree_ignore_exists(self.directory)
