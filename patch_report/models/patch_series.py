from __future__ import absolute_import
import collections
import os

from patch_report import config
from patch_report.models import patch


class PatchSeriesFileNotFound(Exception):
    pass


class PatchSeries(object):
    def __init__(self, repo):
        self.repo = repo
        self.patches = []

    def refresh(self):
        series_path = os.path.join(self.repo.path, 'series')

        if not os.path.exists(series_path):
            if self.repo.patch_report.ignore_missing_series_file:
                return
            else:
                raise PatchSeriesFileNotFound(series_path)

        idx = 1
        repo = self.repo
        patches = self.patches
        with open(series_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                p = patch.Patch(repo, line, idx=idx)
                p.refresh()
                patches.append(p)
                idx += 1

    def get_author_counts(self):
        counter = collections.Counter()
        for patch in self.patches:
            counter[patch.author] += 1

        author_counts = []
        for author, count in counter.iteritems():
            author_counts.append({'author': author, 'count': count})

        return author_counts

    def get_category_counts(self):
        # Count categories
        counter = collections.Counter()
        for patch in self.patches:
            counter[patch.category] += 1

        # Return in a Jinja-friendly format (works well with filters)
        category_counts = []
        for category, count in counter.iteritems():
            category_counts.append({'category': category, 'count': count})

        return category_counts

    def get_overview_counts(self):
        num_patches = len(self.patches)
        num_files = sum(len(p.files) for p in self.patches)
        num_lines = sum(p.line_count for p in self.patches)
        num_upstream_reviews = sum(
                p.upstream_review_count for p in self.patches)
        return {
            'num_files': num_files,
            'num_lines': num_lines,
            'num_patches': num_patches,
            'num_upstream_reviews': num_upstream_reviews,
            'repo': self.repo.name,
        }

    def get_upstream_reviews(self):
        # You'd think a generator would be a good idea here. But then you'd
        # think wrong.
        #
        # The problem is that when we can't use it in a template twice,
        # because we will have exhausted the iterator on the first run.
        # `iter` won't save the day because it's not available in Jinja
        # templates (and I don't feel like passing it in)
        reviews = []
        for patch in self.patches:
            for upstream_review in patch.upstream_reviews:
                reviews.append(upstream_review)
        return reviews
