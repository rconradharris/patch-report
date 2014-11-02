from __future__ import absolute_import
import datetime
import os
import subprocess
try:
    from subprocess import DEVNULL # py3k
except ImportError:
    DEVNULL = open(os.devnull, 'wb')

PIPE = subprocess.PIPE

from patch_report import simplelog
from patch_report import utils
from patch_report.models.patch import Patch
from patch_report.models.patch_activity import PatchActivity


class Repo(object):
    def __init__(self, patch_report, remote_repo):
        self.patch_report = patch_report
        self.remote_repo = remote_repo
        self.activities = []

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

    def _git_cmd(self, pipe, cmd, *args):
        p = subprocess.Popen(('git', cmd) + args,
                             stdout=pipe,
                             stderr=pipe)
        stdout, stderr = p.communicate()
        assert p.returncode == 0
        return stdout, stderr

    def git_show_at_commit(self, path, commit_hash):
        with utils.temp_chdir(self.path):
            return self._git_cmd(PIPE, 'show',
                                 '%s:%s' % (commit_hash, path))[0]

    def _get_parent_commit_hash(self, commit_hash):
        with utils.temp_chdir(self.path):
            stdout = self._git_cmd(PIPE, 'show', commit_hash + '^',
                                   '--pretty=%H')[0]
            return stdout.split('\n')[0].strip()

    def get_patch_activities(self, since):
        since = since.strftime("%Y-%m-%d")
        with utils.temp_chdir(self.path):
            stdout = self._git_cmd(PIPE, 'log', '--summary', '-M',
                                   '--pretty=%H %ct', '--since', since)[0]
        if not stdout:
            return []

        activities = []
        when = None
        for line in stdout.split('\n'):
            line = line.strip()
            if not line:
                continue

            parts = line.split()

            if not parts:
                continue
            elif len(parts) == 2:
                commit_hash = parts[0]
                epoch_secs = int(parts[1])
                when = datetime.datetime.utcfromtimestamp(epoch_secs)
                continue

            what = parts[0]
            if what == 'create':
                filename = parts[3]
                patch = Patch(self, filename, commit_hash=commit_hash)
                activity = PatchActivity(self, when, what, patch)
                activities.append(activity)
            elif what == 'delete':
                filename = parts[3]
                parent_hash = self._get_parent_commit_hash(commit_hash)
                patch = Patch(self, filename, commit_hash=parent_hash)
                activity = PatchActivity(self, when, what, patch)
                activities.append(activity)
            elif what == 'rename':
                filename = parts[3]
                patch = Patch(self, filename, commit_hash=commit_hash)
                activity = PatchActivity(self, when, what, patch,
                                         old_filename=parts[1]) 
                activities.append(activity)

        return activities

    def _refresh_git(self):
        pipe = None if simplelog.is_verbose() else DEVNULL

        if os.path.exists(self.path):
            with utils.temp_chdir(self.path):
                self._git_cmd(pipe, 'checkout', 'master')
                self._git_cmd(pipe, 'fetch', 'origin')
                self._git_cmd(pipe, 'merge', 'origin/master')
        else:
            with utils.temp_chdir(os.path.dirname(self.path)):
                self._git_cmd(pipe, 'clone', self.ssh_url)

    def _refresh_patch_activities(self):
        activity_days = self.patch_report.patch_activity_days

        since = (datetime.datetime.utcnow() -
                 datetime.timedelta(days=activity_days)).date()

        for activity in self.get_patch_activities(since):
            self.activities.append(activity)

    def refresh(self):
        self._refresh_git()
        self.patch_series.refresh()
        self._refresh_patch_activities()
