import os

from patch_report import config
from patch_report import cache
from patch_report import utils
from patch_report.models import patch_series


def get_projects():
    pass



def _get_project(name, patch_series):
    repo_path = config.get_for_project(name, 'repo_path')
    github_url = config.get_for_project(name, 'github_url')
    return Project(name, repo_path, github_url, patch_series)


def get_project(name):
    patch_series = patch_series.PatchSeries(self)
    return _get_project(name, patch_series)


def get_project_from_cache(name):
    patch_series = cache.read_file(name)
    return _get_project(name, patch_series)



class Project(object):
    def __init__(self, name, repo_path, github_url, patch_series):
        self.name = name
        self.repo_path = repo_path
        self.github_url = github_url
        self.patch_series = patch_series

    def refresh(self):
        if os.path.exists(self.repo_path):
            with utils.temp_chdir(self.repo_path):
                os.system('git checkout master && git fetch origin'
                          ' && git merge origin/master')

        self.patch_series.refresh()
        cache.write_file(self.name, self.patch_series)
