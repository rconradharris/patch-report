from __future__ import absolute_import
import datetime
import os

from patch_report import cache
from patch_report import utils


class Repo(object):
    def __init__(self, patch_report, name, url, ssh_url):
        self.patch_report = patch_report
        self.name = name
        self.url = url
        self.ssh_url = ssh_url

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
        return cache.get_last_updated_at(self.name)

    def is_data_stale(self, stale_secs=600):
        utcnow = datetime.datetime.utcnow()
        updated_secs = (utcnow - self.last_updated_at).total_seconds()
        return updated_secs > stale_secs
