import os
import pickle

from patch_report import config
from patch_report.models import patch_series
from patch_report import utils


def _get_project_state_file(project):
    datadir = config.get('patch_report', 'data_directory')
    return os.path.join(datadir, '%s.pickle' % project)


def _refresh_project(project):
    repo_path = config.get_for_project(project, 'repo_path')

    with utils.temp_chdir(repo_path):
        os.system('git checkout master && git fetch origin'
                  ' && git merge origin/master')

    ps = patch_series.PatchSeries(project)
    ps.refresh()

    path = _get_project_state_file(project)
    with open(path, 'w') as f:
        pickle.dump(ps, f)


def refresh_projects():
    projects = config.get_projects()
    for project in projects:
        _refresh_project(project)


def get_patch_series(project):
    path = _get_project_state_file(project)
    with open(path) as f:
        return pickle.load(f)


def get_last_updated_at(project):
    path = _get_project_state_file(project)
    return utils.get_file_modified_time(path)
