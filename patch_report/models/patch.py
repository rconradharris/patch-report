from __future__ import absolute_import
import datetime
import email
import os

from patch_report import config
from patch_report.models import gerrit_review
from patch_report.models import redmine_issue


class Patch(object):
    def __init__(self, repo, filename, idx=None):
        self.repo = repo
        self.filename = filename
        self.idx = idx

        self.raw_author = None
        self.author = None
        self.author_email = None
        self.date = None
        self.line_count = None
        self.rm_issues = []
        self.files = []
        self.upstream_reviews = []

    @property
    def category(self):
        parts = self.filename.split('-')
        return parts[0] if len(parts) > 1 else None

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
        return os.path.join(self.repo.html_url, 'blob', 'master', self.filename)

    @property
    def path(self):
        return os.path.join(self.repo.path, self.filename)

    def _get_name_from_raw_author(self):
        author = self.raw_author.split('<', 1)[0].replace('"', '').strip()

        # RFC 2822 encoded author
        text, encoding = email.Header.decode_header(author)[0]
        if encoding:
            author = unicode(text, encoding)
        else:
            author = unicode(text)

        return author

    def _get_email_from_raw_author(self):
        return self.raw_author.split('<', 1)[1].replace('>', '').strip()

    def _parse_author(self, line):
        if not line.startswith('From:'):
            return

        self.raw_author = line.replace('From: ', '')

        self.author = self._get_name_from_raw_author()
        self.author_email = self._get_email_from_raw_author()

    def _parse_date(self, line):
        if not line.startswith('Date:'):
            return

        # Parse RFC 2822 Date
        date_str = line.replace('Date: ', '')
        date_tuple = email.utils.parsedate_tz(date_str)
        epoch_secs = email.utils.mktime_tz(date_tuple)
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
