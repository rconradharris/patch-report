import collections
import os

from patch_report import config
from patch_report.models import patch


class PatchSeries(object):
    def __init__(self):
        self.patches = []

    def refresh(self):
        repo_path = config.get('patch_report', 'repo_path')
        series_path = os.path.join(repo_path, 'series')

        idx = 1
        with open(series_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                p = patch.Patch(idx, line)
                p.refresh()
                self.patches.append(p)
                idx += 1

    def get_sorted_patches(self, sort_key, sort_dir):
        key = lambda p: getattr(p, sort_key)
        reverse = sort_dir == 'desc'
        return sorted(self.patches, key=key, reverse=reverse)

    def get_category_counts(self):
        """If a prefix is detected more than once in a patch filename, it's
        considered a 'category'.
        """
        counter = collections.Counter()
        for patch in self.patches:
            parts = patch.filename.split('-')
            if len(parts) > 1:
                counter[parts[0]] += 1

        category_counts = []
        for category, count in counter.iteritems():
            if count > 1:
                category_counts.append((category, count))

        category_counts.sort(key=lambda x: x[1], reverse=True)
        return category_counts
