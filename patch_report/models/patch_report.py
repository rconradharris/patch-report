from __future__ import absolute_import
import urlparse

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

    def _get_ssh_url(self, url):
        parsed = urlparse.urlparse(url)
        path_parts = parsed.path.split('/')
        # Ignore first slash at [0]
        org = path_parts[1]
        repo = path_parts[2]
        return "git@%(netloc)s:%(org)s/%(repo)s.git" % dict(
                netloc=parsed.netloc, org=org, repo=repo)

    def refresh(self):
        for name in config.get_repo_names():
            url = config.get('repo:%s' % name, 'url')
            ssh_url = self._get_ssh_url(url)
            repo = Repo(self, name, url, ssh_url)
            repo.patch_series = PatchSeries(repo)
            repo.refresh()
            self._repos[name] = repo
