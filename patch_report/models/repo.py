from __future__ import absolute_import
import os
import subprocess
try:
    from subprocess import DEVNULL # py3k
except ImportError:
    DEVNULL = open(os.devnull, 'wb')

from patch_report import logging
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
    def html_url(self):
        return self.remote_repo.html_url

    @property
    def path(self):
        repo_directory = self.patch_report.repo_directory
        repo_name = os.path.basename(self.url)
        return os.path.join(repo_directory, repo_name)

    def _git_cmd(self, cmd, *args):
        if logging.is_verbose():
            stdout = stderr = None
        else:
            stdout = stderr = DEVNULL

        p = subprocess.Popen(('git', cmd) + args,
                             stdout=stdout,
                             stderr=stderr)
        p.communicate()
        assert p.returncode == 0

    def refresh(self):
        if os.path.exists(self.path):
            with utils.temp_chdir(self.path):
                self._git_cmd('checkout', 'master')
                self._git_cmd('fetch', 'origin')
                self._git_cmd('merge', 'origin/master')
        else:
            with utils.temp_chdir(os.path.dirname(self.path)):
                self._git_cmd('clone', self.ssh_url)

        self.patch_series.refresh()
