from __future__ import absolute_import
import os
import re

import redmine

from patch_report import cache
from patch_report import config
from patch_report.simplelog import log


class RedmineException(Exception):
    pass


class RedmineAuthException(RedmineException):
    pass


class RedmineUnknownException(RedmineException):
    pass


_RE_RM_ISSUE = re.compile('RM\s*#*(\d+)', re.IGNORECASE)
_RE_RM_LINK = re.compile('%s/issues/(\d+)' % config.get('redmine', 'url'))
_REDMINE = None


def _load():
    global _REDMINE

    url = config.get('redmine', 'url')
    key = config.get('redmine', 'key')
    verify_cert = config.get('redmine', 'verify_cert')
    _REDMINE = _Redmine(url, key, verify_cert)


def get_from_line(patch, line):
    match = re.search(_RE_RM_ISSUE, line)
    if not match:
        match = re.match(_RE_RM_LINK, line)
    if not match:
        return

    issue_id = match.group(1)

    if _REDMINE is None:
        _load()

    return _REDMINE.get_issue(patch, issue_id)


class RedmineIssue(object):
    def __init__(self, patch, issue_id, subject=None, status=None,
                 fetch_status='not_fetched'):
        self.patch = patch
        self.issue_id = issue_id
        self._subject = subject
        self.status = status
        self.fetch_status = fetch_status

    @property
    def subject(self):
        s = self.fetch_status

        if s == 'auth_error':
            subject = '<Auth Error>'
        elif s == 'forbidden':
            subject = '<Forbidden>'
        elif s == 'not_fetched':
            subject = '<Not Fetched>'
        elif s == 'not_found':
            subject = '<Not Found>'
        elif s == 'success':
            subject = self._subject
        elif s == 'unknown_error':
            subject = '<Unknown Error>'
        else:
            raise Exception("Unknown fetch_status: '%s'" % s)

        return subject

    @property
    def url(self):
        base = config.get('redmine', 'url')
        return os.path.join(base, 'issues', self.issue_id)

    def __eq__(self, other):
        return self.issue_id == other.issue_id


class _Redmine(object):
    def __init__(self, url, key, verify_cert):
        self.url = url
        self.key = key
        self.verify_cert = verify_cert
        self.cache = cache.DictCache('redmine_issues')
        self.ignore_errors = config.get('redmine', 'ignore_errors')
        self.last_unrecoverable_error = None
        self.redmine = redmine.Redmine(url,
                                       requests={'verify': verify_cert},
                                       key=key,
                                       raise_attr_exception=True)

    def _fetch_remote_issue(self, patch, issue_id):
        log('Fetching Redmine Issue %s' % issue_id)

        status =  None
        subject = None

        if self.last_unrecoverable_error:
            fetch_status = self.last_unrecoverable_error
        else:
            try:
                issue = self.redmine.issue.get(issue_id)
            except redmine.exceptions.UnknownError as unknown_ex:
                # FIXME: we can use ForbiddenError here if
                # https://github.com/maxtepkeev/python-redmine/pull/60 merges
                if '403' in unknown_ex.message:
                    fetch_status = 'forbidden'
                elif not self.ignore_errors:
                    raise RedmineUnknownException(unknown_ex.message)
                else:
                    self.last_unrecoverable_error = \
                            fetch_status = 'unknown_error'
            except redmine.exceptions.AuthError as auth_ex:
                self.last_unrecoverable_error = \
                        fetch_status = 'auth_error'
                if not self.ignore_errors:
                    raise RedmineAuthException(
                        "Authentication error: %s" % auth_ex)
            except redmine.exceptions.ResourceNotFoundError as res_ex:
                fetch_status = 'not_found'
            else:
                subject = issue.subject
                status = issue.status.name
                fetch_status = 'success'

        return RedmineIssue(patch, issue_id, subject=subject, status=status,
                            fetch_status=fetch_status)

    def get_issue(self, patch, issue_id):
        try:
            issue = self.cache[issue_id]
        except KeyError:
            pass
        else:
            return issue

        issue = self._fetch_remote_issue(patch, issue_id)
        self.cache[issue_id] = issue
        return issue
