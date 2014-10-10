import os
import pickle

from patch_report import config
from patch_report.models import patch_series
from patch_report import utils


def _get_save_path():
    datadir = config.get('patch_report', 'data_directory')
    return os.path.join(datadir, 'repo_state.pickle')


def refresh_patch_series():
    repo_path = config.get('patch_report', 'repo_path')

    with utils.temp_chdir(repo_path):
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
    return utils.get_file_modified_time(path)
