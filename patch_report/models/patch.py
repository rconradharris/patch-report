from __future__ import absolute_import
import datetime
import email
import os
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from patch_report import config
from patch_report.models import gerrit_review
from patch_report.models import redmine_issue


def _parse_author_name(line):
    line = line.replace('From: ', '')
    author_name = line.split('<', 1)[0].replace('"', '').strip()

    # RFC 2822 encoded author_name
    text, encoding = email.Header.decode_header(author_name)[0]
    if encoding:
        author_name = unicode(text, encoding)
    else:
        author_name = unicode(text)

    return author_name


def _parse_author_email(line):
    line = line.replace('From: ', '')
    return line.split('<', 1)[1].replace('>', '').strip()


def _parse_author_date(line):
    line = line.replace('Date: ', '')

    # Parse RFC 2822 Date
    date_tuple = email.utils.parsedate_tz(line)
    epoch_secs = email.utils.mktime_tz(date_tuple)
    date = datetime.datetime.fromtimestamp(epoch_secs)
    return date


def _parse_subject(line):
    line = line.replace('Subject: ', '')
    line = line.rstrip('\n')
    return line


def _parse_diff_filename(line):
    filename = line.rstrip('\n').split(' ')[-1]
    filename = filename[2:]  # Remove 'b/'
    return filename


def _strip_trailing_blank_lines_from_commit_message(commit_lines):
    while commit_lines:
        if commit_lines[-1]:
            break
        else:
            commit_lines.pop()


def _parse_metadata(file_or_string):
    if hasattr(file_or_string, 'close'):
        f = file_or_string
    else:
        f = StringIO.StringIO(file_or_string)

    parse_commit_message = False
    commit_lines = []
    filenames = []
    line_count = 0
    for line in f:
        line_count += 1
        if not line:
            continue
        elif line.startswith('From ply'):
            continue
        elif line.startswith('diff --git'):
            filename = _parse_diff_filename(line)
            filenames.append(filename)
            parse_commit_message = False
        elif line.startswith('From:'):
            author_name = _parse_author_name(line)
            author_email = _parse_author_email(line)
        elif line.startswith('Date:'):
            author_date = _parse_author_date(line)
        elif line.startswith('Subject:'):
            subject = _parse_subject(line)
            commit_lines.append(subject)
            parse_commit_message = True
        else:
            if parse_commit_message:
                assert commit_lines, line
                line = line.rstrip('\n')
                commit_lines.append(line)

    _strip_trailing_blank_lines_from_commit_message(commit_lines)
    commit_message = '\n'.join(commit_lines)

    return {
        'author': author_name,
        'author_email': author_email,
        'date': author_date,
        'commit_message': commit_message,
        'files': filenames,
        'line_count': line_count,
    }


class Patch(object):
    def __init__(self, repo, filename, idx=None, commit_hash='master'):
        self.repo = repo
        self.filename = filename
        self.idx = idx
        self.commit_hash = commit_hash

        self.author = ''
        self.author_email = ''
        self.date = None
        self.line_count = 0
        self.files = []
        self.commit_message = ''

        self.rm_issues = []
        self.upstream_reviews = []

    def __repr__(self):
        return '<Patch {0}>'.format(self.filename)

    @property
    def subject(self):
        return self.commit_message.split('\n')[0]

    @property
    def category(self):
        subject = self.subject

        if ':' not in subject:
            return None

        return subject.split(':', 1)[0]

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
        return os.path.join(self.repo.html_url, 'blob', self.commit_hash, self.filename)

    @property
    def path(self):
        return os.path.join(self.repo.path, self.filename)

    def _parse_rm_issue(self, line):
        rm_issue = redmine_issue.get_from_line(self, line)
        # Avoid dup if there's a tag *and* a link
        if rm_issue and rm_issue not in self.rm_issues:
            self.rm_issues.append(rm_issue)

    def _parse_upstream_change_id(self, line):
        gr = gerrit_review.get_from_line(self, line)
        if gr:
            self.upstream_reviews.append(gr)

    @property
    def contents(self):
        return self.repo.git_show_at_commit(self.filename, self.commit_hash)

    def refresh(self):
        metadata = _parse_metadata(self.contents)
        for attr, val in metadata.iteritems():
            setattr(self, attr, val)

        for line in self.commit_message.split('\n'):
            self._parse_rm_issue(line)
            self._parse_upstream_change_id(line)
