import os

from patch_report import cache
from patch_report import config
from patch_report.models import patch_series
from patch_report import utils


def _refresh_project(project):
    repo_path = config.get_for_project(project, 'repo_path')

    with utils.temp_chdir(repo_path):
        os.system('git checkout master && git fetch origin'
                  ' && git merge origin/master')

    ps = patch_series.PatchSeries(project)
    ps.refresh()

    cache.write_file(project, ps)


def refresh_projects():
    projects = config.get_projects()
    for project in projects:
        _refresh_project(project)


def get_patch_series(project):
    return cache.read_file(project)


def get_last_updated_at(project):
    return cache.get_last_updated_at(project)
