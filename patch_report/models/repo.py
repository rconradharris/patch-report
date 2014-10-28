from __future__ import absolute_import
import datetime
import os

from patch_report import cache
from patch_report import utils


class Repo(object):
    def __init__(self, patch_report, remote_repo):
        self.patch_report = patch_report
        self.remote_repo = remote_repo

    @property
    def name(self):
        return self.remote_repo.name

    @property
    def url(self):
        return self.remote_repo.url

    @property
    def ssh_url(self):
        return self.remote_repo.ssh_url

    @property
    def path(self):
        repo_directory = self.patch_report.repo_directory
        repo_name = os.path.basename(self.url)
        return os.path.join(repo_directory, repo_name)

    def refresh(self):
        if os.path.exists(self.path):
            with utils.temp_chdir(self.path):
                os.system('git checkout master && git fetch origin'
                          ' && git merge origin/master')
        else:
            with utils.temp_chdir(os.path.dirname(self.path)):
                os.system('git clone %s' % self.ssh_url)

        self.patch_series.refresh()

    @property
    def last_updated_at(self):
        return cache.get_last_updated_at('patch_report')

    def is_data_stale(self, stale_secs=600):
        utcnow = datetime.datetime.utcnow()
        updated_secs = (utcnow - self.last_updated_at).total_seconds()
        return updated_secs > stale_secs
