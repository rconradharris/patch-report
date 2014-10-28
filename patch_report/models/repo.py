from __future__ import absolute_import
import datetime
import os
import urlparse

from patch_report import cache
from patch_report import config
from patch_report import utils
from patch_report.models import patch_series


class Repo(object):
    def __init__(self, patch_report, name, url):
        self.patch_report = patch_report
        self.name = name
        self.url = url

    @property
    def path(self):
        repo_directory = self.patch_report.repo_directory
        repo_name = os.path.basename(self.url)
        return os.path.join(repo_directory, repo_name)

    def _get_github_ssh_url(self):
        parsed = urlparse.urlparse(self.url)
        path_parts = parsed.path.split('/')
        # Ignore first slash at [0]
        org = path_parts[1]
        repo = path_parts[2]
        return "git@%(netloc)s:%(org)s/%(repo)s.git" % dict(
                netloc=parsed.netloc, org=org, repo=repo)

    def refresh(self):
        if os.path.exists(self.path):
            with utils.temp_chdir(self.path):
                os.system('git checkout master && git fetch origin'
                          ' && git merge origin/master')
        else:
            ssh_url = self._get_github_ssh_url()
            with utils.temp_chdir(os.path.dirname(self.path)):
                os.system('git clone %s' % ssh_url)

        self.patch_series.refresh()

    @property
    def last_updated_at(self):
        return cache.get_last_updated_at(self.name)

    def is_data_stale(self, stale_secs=600):
        utcnow = datetime.datetime.utcnow()
        updated_secs = (utcnow - self.last_updated_at).total_seconds()
        return updated_secs > stale_secs
