import datetime
import os

from patch_report import config
from patch_report import cache
from patch_report import utils
from patch_report.models import patch_series


def _get_project(name):
    repo_path = config.get_for_project(name, 'repo_path')
    github_url = config.get_for_project(name, 'github_url')
    return Project(name, repo_path, github_url)


def get_project_from_cache(name):
    project = _get_project(name)
    project.patch_series = cache.read_file(name)
    return project


def get_projects_from_cache():
    return [get_project_from_cache(n) for n in config.get_project_names()]


def refresh_projects(clear=False):
    if clear:
        cache.clear()

    for project_name in config.get_project_names():
        project = _get_project(project_name)
        project.patch_series = patch_series.PatchSeries(project)
        project.refresh()


class Project(object):
    def __init__(self, name, repo_path, github_url):
        self.name = name
        self.repo_path = repo_path
        self.github_url = github_url

    def refresh(self):
        if os.path.exists(self.repo_path):
            with utils.temp_chdir(self.repo_path):
                os.system('git checkout master && git fetch origin'
                          ' && git merge origin/master')

        self.patch_series.refresh()
        cache.write_file(self.name, self.patch_series)

    def get_last_updated_at(self):
        return cache.get_last_updated_at(self.name)

    def is_data_stale(self, stale_secs=600):
        utcnow = datetime.datetime.utcnow()
        updated_secs = (utcnow - self.get_last_updated_at()).total_seconds()
        return updated_secs > stale_secs
