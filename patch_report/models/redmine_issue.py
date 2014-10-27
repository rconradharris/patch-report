import os
import re

import redmine

from patch_report import cache
from patch_report import config


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
    username = config.get('redmine', 'username')
    password = config.get('redmine', 'password')
    _REDMINE = _Redmine(url, username, password)


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
    def __init__(self, patch, issue_id, subject=None, status=None):
        self.patch = patch
        self.issue_id = issue_id
        self.subject = subject
        self.status = status

    @property
    def url(self):
        base = config.get('redmine', 'url')
        return os.path.join(base, 'issues', self.issue_id)

    def __eq__(self, other):
        return self.issue_id == other.issue_id


class _Redmine(object):
    def __init__(self, url, username, password, verify_cert=False, debug=True):
        self.url = url
        self.username = username
        self.password = password
        self.verify_cert = verify_cert
        self.debug = debug
        self.cache = cache.DictCache('redmine_issues')
        self.ignore_errors = config.get('redmine', 'ignore_errors')
        self.unrecoverable_error = False
        self.redmine = redmine.Redmine(url,
                                       requests={'verify': verify_cert},
                                       username=username,
                                       password=password,
                                       raise_attr_exception=debug)

    def _fetch_remote_issue(self, issue_id):
        if self.debug:
            print 'Fetching Redmine Issue %s' % issue_id

        status =  None
        subject = None

        if not self.unrecoverable_error:
            try:
                issue = self.redmine.issue.get(issue_id)
            except redmine.exceptions.UnknownError as unknown_ex:
                # FIXME: we can use ForbiddenError here if
                # https://github.com/maxtepkeev/python-redmine/pull/60 merges
                if '403' in unknown_ex.message:
                    pass
                elif not self.ignore_errors:
                    raise RedmineUnknownException(unknown_ex.message)
                else:
                    self.unrecoverable_error = True
            except redmine.exceptions.AuthError as auth_ex:
                self.unrecoverable_error = True
                if not self.ignore_errors:
                    raise RedmineAuthException(
                        "Authentication error: %s" % auth_ex)
            except redmine.exceptions.ResourceNotFoundError as res_ex:
                pass
            else:
                subject = issue.subject
                status = issue.status.name

        return {'subject': subject,
                'status': status}

    def get_issue(self, patch, issue_id):
        try:
            issue = self.cache[issue_id]
        except KeyError:
            pass
        else:
            return issue

        issue_kwargs = self._fetch_remote_issue(issue_id)
        issue = RedmineIssue(patch, issue_id, **issue_kwargs)

        self.cache[issue_id] = issue
        return issue
