from __future__ import absolute_import
import datetime

from patch_report import config
from patch_report import cache
from patch_report.models import github_scanner
from patch_report.models.patch_series import PatchSeries
from patch_report.models.repo import Repo


def get_from_cache():
    return cache.read_file('patch_report')


def refresh():
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
        scanner = github_scanner.get_from_cache()
        for remote_repo in scanner.remote_repos:
            repo = Repo(self, remote_repo)
            repo.patch_series = PatchSeries(repo)
            repo.refresh()
            self._repos[repo.name] = repo

    @property
    def last_updated_at(self):
        return cache.get_last_updated_at('patch_report')

    def is_data_stale(self, stale_secs=600):
        utcnow = datetime.datetime.utcnow()
        updated_secs = (utcnow - self.last_updated_at).total_seconds()
        return updated_secs > stale_secs
