from __future__ import absolute_import
import os
import pickle

import redmine

from patch_report import config


class RedmineException(Exception):
    pass


class RedmineAuthException(RedmineException):
    pass


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
