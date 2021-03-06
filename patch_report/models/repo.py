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
        """Return a selection of patch activities from a given time in
        seconds.

        This uses the patch_report cache so it should be cheaper than actually
        hitting git.
        """
        utcnow = datetime.datetime.utcnow()

        activities = []
        for activity in self.activities:
            age = utcnow - activity.when
            age_secs = age.total_seconds()
            if age_secs < since:
                activities.append(activity)

        return activities

    def get_patch_activities_from_git(self, since):
        """Return all activities since a given time.

        This actually hits git so is more expensive.

        :param since: string containing a time specifier. Could be a date or
                      something like '5 minutes ago'
        """
        def add_activity(filename, commit_hash, old_filename=None):
            if not filename.endswith('.patch'):
                return

            patch = Patch(self, filename, commit_hash=commit_hash)
            patch.refresh()
            activity = PatchActivity(self, commit_hash, when, what, patch,
                                     old_filename=old_filename)
            activities.append(activity)

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
                add_activity(parts[3], commit_hash)
            elif what == 'delete':
                parent_hash = self._get_parent_commit_hash(commit_hash)
                add_activity(parts[3], parent_hash)
            elif what == 'rename':
                add_activity(parts[3], commit_hash, old_filename=parts[1])

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

    def _refresh_patch_activities(self, activity_days=365):
        since = '%d days ago' % activity_days
        for activity in self.get_patch_activities_from_git(since):
            self.activities.append(activity)

    def refresh(self):
        simplelog.log("Refreshing repo '%s'" % self.name)
        self._refresh_git()
        self.patch_series.refresh()
        self._refresh_patch_activities()
