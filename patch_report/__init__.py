import contextlib
import datetime
import os
import pickle

from patch_report import config
from patch_report.models import patch_series


@contextlib.contextmanager
def temp_chdir(dirname):
    orig_path = os.getcwd()
    os.chdir(dirname)
    try:
        yield
    finally:
        os.chdir(orig_path)


def _get_save_path():
    datadir = config.get('patch_report', 'data_directory')
    return os.path.join(datadir, 'repo_state.pickle')


def refresh_patch_series():
    repo_path = config.get('patch_report', 'repo_path')

    with temp_chdir(repo_path):
        os.system('git checkout master && git fetch origin'
                  ' && git merge origin/master')

    ps = patch_series.PatchSeries()
    ps.refresh()

    with open(_get_save_path(), 'w') as f:
        pickle.dump(ps, f)


def get_patch_series():
    with open(_get_save_path()) as f:
        return pickle.load(f)


def get_last_updated_at():
    path = _get_save_path()

    if not os.path.exists(path):
        return None

    epoch_secs = os.path.getmtime(path)
    return datetime.datetime.fromtimestamp(epoch_secs)
