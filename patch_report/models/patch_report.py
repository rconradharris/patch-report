from __future__ import absolute_import
from patch_report import config
from patch_report import cache
from patch_report.models.repo import Repo
from patch_report.models.patch_series import PatchSeries


def get_from_cache():
    return cache.read_file('patch_report')


def refresh(clear_cache=False):
    if clear_cache:
        cache.clear()

    repo_directory = config.get('patch_report', 'repo_directory')
    patch_report = PatchReport(repo_directory)
    patch_report.refresh()

    cache.write_file('patch_report', patch_report)


class PatchReport(object):
    def __init__(self, repo_directory):
        self.repo_directory = repo_directory
        self._repos = {}

    @property
    def repos(self):
        return self._repos.values()

    def get_repo(self, name):
        return self._repos[name]

    def refresh(self):
        for name in config.get_repo_names():
            repo = Repo(self, name)
            repo.patch_series = PatchSeries(repo)
            repo.refresh()
            self._repos[name] = repo
