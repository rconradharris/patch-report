import collections
import os

from patch_report import config
from patch_report.models import patch


class PatchSeries(object):
    def __init__(self, project):
        self.project = project
        self.patches = []

    def refresh(self):
        repo_path = config.get_for_project(self.project, 'repo_path')
        series_path = os.path.join(repo_path, 'series')

        idx = 1
        with open(series_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                p = patch.Patch(self, idx, line)
                p.refresh()
                self.patches.append(p)
                idx += 1

    def get_sorted_patches(self, sort_key, sort_dir):
        key = lambda p: getattr(p, sort_key)
        reverse = sort_dir == 'desc'
        return sorted(self.patches, key=key, reverse=reverse)

    def get_author_counts(self):
        counter = collections.Counter()
        for patch in self.patches:
            counter[patch.author] += 1

        author_counts = []
        for author, count in counter.iteritems():
            author_counts.append({'author': author, 'count': count})

        return author_counts

    def get_category_counts(self):
        """If a prefix is detected more than once in a patch filename, it's
        considered a 'category'.
        """
        # Count categories
        counter = collections.Counter()
        for patch in self.patches:
            parts = patch.filename.split('-')
            category = parts[0] if len(parts) > 1 else None
            counter[category] += 1

        # Group None-valued categories
        counter2 = collections.Counter()
        for category, count in counter.iteritems():
            if count < 2:
                category = None
            counter2[category] += count

        # Return in a Jinja-friendly format (works well with filters)
        category_counts = []
        for category, count in counter2.iteritems():
            category_counts.append({'category': category, 'count': count})

        return category_counts

    def get_overview_counts(self):
        num_patches = len(self.patches)
        num_files = sum(len(p.files) for p in self.patches)
        num_lines = sum(p.line_count for p in self.patches)
        return {
            'num_files': num_files,
            'num_lines': num_lines,
            'num_patches': num_patches,
        }

