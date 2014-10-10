import contextlib
import datetime
from email.utils import parsedate_tz, mktime_tz
import os
import pickle
import re

import redmine

from patch_report import config


@contextlib.contextmanager
def temp_chdir(dirname):
    orig_path = os.getcwd()
    os.chdir(dirname)
    try:
        yield
    finally:
        os.chdir(orig_path)


class GerritReview(object):
    BASE_URL = "https://review.openstack.org/#q,%s,n,z"

    def __init__(self, change_id):
        self.change_id = change_id

    @property
    def url(self):
        return self.BASE_URL % self.change_id


class RedmineException(Exception):
    pass


class RedmineAuthException(RedmineException):
    pass


class Redmine(object):
    def __init__(self, url, username, password, verify_cert=False, debug=True):
        self.url = url
        self.username = username
        self.password = password
        self.verify_cert = verify_cert
        self.debug = debug

        self.redmine = redmine.Redmine(url,
                                       requests={'verify': verify_cert},
                                       username=username,
                                       password=password,
                                       raise_attr_exception=debug)

    def _fetch_remote_issue(self, issue_id):
        if self.debug:
            print 'Fetching Redmine Issue %s' % issue_id

        try:
            issue = self.redmine.issue.get(issue_id)
        except redmine.exceptions.AuthError as auth_ex:
            raise RedmineAuthException(
                "Authentication error: %s" % auth_ex)
        except redmine.exceptions.ResourceNotFoundError as res_ex:
            subject = None
            status = None
        else:
            subject = issue.subject
            status = issue.status.name

        return {'subject': subject,
                'status': status}

    @property
    def _cache_path(self):
        datadir = config.get('patch_report', 'data_directory')
        return os.path.join(datadir, 'redmine_issues.pickle')

    @property
    def cached_issues(self):
        if not hasattr(self, '_cached_issues'):
            if os.path.exists(self._cache_path):
                with open(self._cache_path) as f:
                    self._cached_issues = pickle.load(f)
            else:
                self._cached_issues = {}

        return self._cached_issues

    def _add_cached_issue(self, issue):
        self.cached_issues[issue.issue_id] = issue
        with open(self._cache_path, 'w') as f:
            pickle.dump(self.cached_issues, f)

    def get_issue(self, issue_id):
        issue = self.cached_issues.get(issue_id)
        if issue:
            return issue

        issue_kwargs = self._fetch_remote_issue(issue_id)
        issue = RedmineIssue(issue_id, **issue_kwargs)

        self._add_cached_issue(issue)
        return issue


class RedmineIssue(object):
    BASE_URL = "https://redmine.ohthree.com/issues"

    def __init__(self, issue_id, subject=None, status=None):
        self.issue_id = issue_id
        self.subject = subject
        self.status = status

    @property
    def url(self):
        return os.path.join(self.BASE_URL, self.issue_id)

    def __eq__(self, other):
        return self.issue_id == other.issue_id


class Patch(object):
    GITHUB_URL = "https://github.rackspace.com/O3Eng/nova-rax-patches/blob"\
                 "/master"

    RE_RM_ISSUE = re.compile('RM\s*#*(\d+)', re.IGNORECASE)
    RE_RM_LINK = re.compile('https://redmine.ohthree.com/issues/(\d+)')

    # FIXME: Until UTF-8 is supported...
    NAME_OVERRIDES = {'=?UTF-8?q?Jason=20K=C3=B6lker?=': 'Jason Koelker'}

    def __init__(self, patch_report, idx, filename):
        self.patch_report = patch_report
        self.idx = idx
        self.filename = filename

        self.raw_author = None
        self.author = None
        self.author_email = None
        self.date = None
        self.line_count = None
        self.rm_issues = []
        self.files = []
        self.gerrit_reviews = []

    @property
    def rm_issue_count(self):
        return len(self.rm_issues)

    @property
    def gerrit_review_count(self):
        return len(self.gerrit_reviews)

    @property
    def file_count(self):
        return len(self.files)

    @property
    def url(self):
        return os.path.join(self.GITHUB_URL, self.filename)

    @property
    def path(self):
        return os.path.join(self.patch_report.path, self.filename)

    def _parse_author(self, line):
        if not line.startswith('From:'):
            return

        self.raw_author = line.replace('From: ', '')
        self.author, self.author_email = self.raw_author.split('<', 1)

        self.author = self.author.strip()
        if self.author in self.NAME_OVERRIDES:
            self.author = self.NAME_OVERRIDES[self.author]
        self.author = self.author.replace('"', '')

        self.author_email = self.author_email.replace('>', '')
        self.author_email = self.author_email.strip()

    def _parse_date(self, line):
        if not line.startswith('Date:'):
            return

        # Parse RFC 2822 Date
        date_str = line.replace('Date: ', '')
        date_tuple = parsedate_tz(date_str)
        epoch_secs = mktime_tz(date_tuple)
        self.date = datetime.datetime.fromtimestamp(epoch_secs)

    def _parse_rm_issue(self, line):
        match = re.search(self.RE_RM_ISSUE, line)
        if not match:
            match = re.match(self.RE_RM_LINK, line)
        if match:
            issue_id = match.group(1)
            rm_issue = self.patch_report.redmine.get_issue(issue_id)
            # Avoid dup if there's a tag *and* a link
            if rm_issue not in self.rm_issues:
                self.rm_issues.append(rm_issue)

    def _parse_diff_file_line(self, line):
        if 'diff --git' not in line:
            return

        b_part = line.split(' ')[-1]
        b_part = b_part[2:]  # Remove 'b/'
        self.files.append(b_part)

    def _parse_upstream_change_id(self, line):
        if 'Upstream-Change-Id' not in line:
            return

        change_id = line.split(' ', 1)[1].strip()
        gr = GerritReview(change_id)
        self.gerrit_reviews.append(gr)

    def refresh(self):
        line_count = 0
        with open(self.path) as f:
            for line in f:
                line_count += 1
                line = line.strip()
                if not line:
                    continue
                for name in dir(self):
                    if name.startswith('_parse'):
                        func = getattr(self, name)
                        func(line)
        self.line_count = line_count


class PatchReport(object):
    def __init__(self):
        self.patches = []

    @property
    def path(self):
        return config.get('patch_report', 'repo_path')

    @property
    def redmine(self):
        url = config.get('redmine', 'url')
        username = config.get('redmine', 'username')
        password = config.get('redmine', 'password')
        return Redmine(url, username, password)

    def get_sorted_patches(self, sort_key, sort_dir):
        key = lambda p: getattr(p, sort_key)
        reverse = sort_dir == 'desc'
        return sorted(self.patches, key=key, reverse=reverse)

    def refresh(self):
        with temp_chdir(self.path):
            os.system('git checkout master && git fetch origin && git merge origin/master')

        idx = 1
        with open(os.path.join(self.path, 'series')) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                patch = Patch(self, idx, line)
                patch.refresh()
                self.patches.append(patch)
                idx += 1

    @staticmethod
    def _get_save_path():
        datadir = config.get('patch_report', 'data_directory')
        return os.path.join(datadir, 'repo_state.pickle')

    def save(self):
        with open(self._get_save_path(), 'w') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls):
        with open(cls._get_save_path()) as f:
            patch_report = pickle.load(f)
        return patch_report

    @classmethod
    def get_last_updated_at(cls):
        path = cls._get_save_path()

        if not os.path.exists(path):
            return None

        epoch_secs = os.path.getmtime(path)
        return datetime.datetime.fromtimestamp(epoch_secs)
