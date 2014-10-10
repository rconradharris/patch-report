import contextlib
import datetime
import os
import pickle

from patch_report import config
from patch_report.models import patch
from patch_report.models import redmine


@contextlib.contextmanager
def temp_chdir(dirname):
    orig_path = os.getcwd()
    os.chdir(dirname)
    try:
        yield
    finally:
        os.chdir(orig_path)


class PatchReport(object):
    def __init__(self):
        self.patches = []

    @property
    def path(self):
        return config.get('patch_report', 'repo_path')

    @property
    def redmine(self):
        url = config.get('redmine', 'url')
        username = config.get('redmine', 'username')
        password = config.get('redmine', 'password')
        return redmine.Redmine(url, username, password)

    def get_sorted_patches(self, sort_key, sort_dir):
        key = lambda p: getattr(p, sort_key)
        reverse = sort_dir == 'desc'
        return sorted(self.patches, key=key, reverse=reverse)

    def refresh(self):
        with temp_chdir(self.path):
            os.system('git checkout master && git fetch origin && git merge origin/master')

        idx = 1
        with open(os.path.join(self.path, 'series')) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                p = patch.Patch(self, idx, line)
                p.refresh()
                self.patches.append(p)
                idx += 1

        with open(self._get_save_path(), 'w') as f:
            pickle.dump(self, f)

    @staticmethod
    def _get_save_path():
        datadir = config.get('patch_report', 'data_directory')
        return os.path.join(datadir, 'repo_state.pickle')

    @classmethod
    def load(cls):
        with open(cls._get_save_path()) as f:
            patch_report = pickle.load(f)
        return patch_report

    @classmethod
    def get_last_updated_at(cls):
        path = cls._get_save_path()

        if not os.path.exists(path):
            return None

        epoch_secs = os.path.getmtime(path)
        return datetime.datetime.fromtimestamp(epoch_secs)
