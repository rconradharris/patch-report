from __future__ import absolute_import
import datetime
from email.utils import parsedate_tz, mktime_tz
import os

from patch_report import config
from patch_report.models import gerrit_review
from patch_report.models import redmine_issue


class Patch(object):
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
        self.upstream_reviews = []

    @property
    def repo(self):
        return self.patch_series.repo

    @property
    def rm_issue_count(self):
        return len(self.rm_issues)

    @property
    def upstream_review_count(self):
        return len(self.upstream_reviews)

    @property
    def all_upstream_reviews_merged(self):
        return all(r.is_merged for r in self.upstream_reviews)

    @property
    def file_count(self):
        return len(self.files)

    @property
    def url(self):
        return os.path.join(self.repo.url, 'blob', 'master', self.filename)

    @property
    def path(self):
        return os.path.join(self.repo.path, self.filename)

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
        rm_issue = redmine_issue.get_from_line(self, line)
        # Avoid dup if there's a tag *and* a link
        if rm_issue and rm_issue not in self.rm_issues:
            self.rm_issues.append(rm_issue)

    def _parse_diff_file_line(self, line):
        if 'diff --git' not in line:
            return

        b_part = line.split(' ')[-1]
        b_part = b_part[2:]  # Remove 'b/'
        self.files.append(b_part)

    def _parse_upstream_change_id(self, line):
        gr = gerrit_review.get_from_line(self, line)
        if gr:
            self.upstream_reviews.append(gr)

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
