import os
import re

import redmine

from patch_report import cache
from patch_report import config


class RedmineException(Exception):
    pass


class RedmineAuthException(RedmineException):
    pass


CACHE_FILE = 'redmine_issues'
RE_RM_ISSUE = re.compile('RM\s*#*(\d+)', re.IGNORECASE)
RE_RM_LINK = re.compile('%s/issues/(\d+)' % config.get('redmine', 'url'))
_REDMINE = None


def _load():
    global _REDMINE

    url = config.get('redmine', 'url')
    username = config.get('redmine', 'username')
    password = config.get('redmine', 'password')
    _REDMINE = Redmine(url, username, password)


def get_issue(issue_id):
    if _REDMINE is None:
        _load()

    return _REDMINE.get_issue(issue_id)


def get_from_line(line):
    match = re.search(RE_RM_ISSUE, line)
    if not match:
        match = re.match(RE_RM_LINK, line)
    if not match:
        return

    issue_id = match.group(1)
    return get_issue(issue_id)


class RedmineIssue(object):
    def __init__(self, issue_id, subject=None, status=None):
        self.issue_id = issue_id
        self.subject = subject
        self.status = status

    @property
    def url(self):
        base = config.get('redmine', 'url')
        return os.path.join(base, 'issues', self.issue_id)

    def __eq__(self, other):
        return self.issue_id == other.issue_id


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
    def cached_issues(self):
        if not hasattr(self, '_cached_issues'):
            try:
                self._cached_issues = cache.read_file(CACHE_FILE)
            except cache.CacheFileNotFound:
                self._cached_issues = {}

        return self._cached_issues

    def _add_cached_issue(self, issue):
        self.cached_issues[issue.issue_id] = issue
        cache.write_file(CACHE_FILE, self.cached_issues)

    def get_issue(self, issue_id):
        issue = self.cached_issues.get(issue_id)
        if issue:
            return issue

        issue_kwargs = self._fetch_remote_issue(issue_id)
        issue = RedmineIssue(issue_id, **issue_kwargs)

        self._add_cached_issue(issue)
        return issue
