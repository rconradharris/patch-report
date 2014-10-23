import datetime
from email.utils import parsedate_tz, mktime_tz
import os
import re

from patch_report import config
from patch_report.models import gerrit
from patch_report.models import redmine


class Patch(object):
    RE_RM_ISSUE = re.compile('RM\s*#*(\d+)', re.IGNORECASE)
    RE_RM_LINK = re.compile('%s/issues/(\d+)' % config.get('redmine', 'url'))

    # FIXME: Until UTF-8 is supported...
    NAME_OVERRIDES = {'=?UTF-8?q?Jason=20K=C3=B6lker?=': 'Jason Koelker'}

    def __init__(self, patch_series, idx, filename):
        self.patch_series = patch_series
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
    def project(self):
        return self.patch_series.project

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
        base_url = config.get_for_project(self.project, 'github_url')
        return os.path.join(base_url, 'blob', 'master', self.filename)

    @property
    def path(self):
        repo_path = config.get_for_project(self.project, 'repo_path')
        return os.path.join(repo_path, self.filename)

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
            rm_issue = redmine.get_issue(issue_id)
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
        gr = gerrit.GerritReview(change_id)
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
